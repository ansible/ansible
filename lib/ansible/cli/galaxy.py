# Copyright: (c) 2013, James Cammarata <jcammarata@ansible.com>
# Copyright: (c) 2018, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os.path
import re
import shutil
import textwrap
import time
import yaml

from jinja2 import BaseLoader, Environment, FileSystemLoader

import ansible.constants as C
from ansible import context
from ansible.cli import CLI
from ansible.cli.arguments import option_helpers as opt_help
from ansible.errors import AnsibleError, AnsibleOptionsError
from ansible.galaxy import Galaxy, get_collections_galaxy_meta_info
from ansible.galaxy.api import GalaxyAPI
from ansible.galaxy.collection import build_collection, install_collections, parse_collections_requirements_file, \
    publish_collection
from ansible.galaxy.login import GalaxyLogin
from ansible.galaxy.role import GalaxyRole
from ansible.galaxy.token import GalaxyToken
from ansible.module_utils.ansible_release import __version__ as ansible_version
from ansible.module_utils._text import to_bytes, to_native, to_text
from ansible.playbook.role.requirement import RoleRequirement
from ansible.utils.collection_loader import is_collection_ref
from ansible.utils.display import Display
from ansible.utils.plugin_docs import get_versioned_doclink

display = Display()


class GalaxyCLI(CLI):
    '''command to manage Ansible roles in shared repositories, the default of which is Ansible Galaxy *https://galaxy.ansible.com*.'''

    SKIP_INFO_KEYS = ("name", "description", "readme_html", "related", "summary_fields", "average_aw_composite", "average_aw_score", "url")

    def __init__(self, args):
        # Inject role into sys.argv[1] as a backwards compatibility step
        if len(args) > 1 and args[1] not in ['-h', '--help'] and 'role' not in args and 'collection' not in args:
            # TODO: Should we add a warning here and eventually deprecate the implicit role subcommand choice
            args.insert(1, 'role')

        self.api = None
        self.galaxy = None
        super(GalaxyCLI, self).__init__(args)

    def init_parser(self):
        ''' create an options parser for bin/ansible '''

        super(GalaxyCLI, self).init_parser(
            desc="Perform various Role and Collection related operations.",
        )

        # common
        common = opt_help.argparse.ArgumentParser(add_help=False)
        common.add_argument('-s', '--server', dest='api_server', default=C.GALAXY_SERVER, help='The API server destination')
        common.add_argument('-c', '--ignore-certs', action='store_true', dest='ignore_certs', default=C.GALAXY_IGNORE_CERTS,
                            help='Ignore SSL certificate validation errors.')
        opt_help.add_verbosity_options(common)

        # options that apply to more than one action
        user_repo = opt_help.argparse.ArgumentParser(add_help=False)
        user_repo.add_argument('github_user', help='GitHub username')
        user_repo.add_argument('github_repo', help='GitHub repository')

        offline = opt_help.argparse.ArgumentParser(add_help=False)
        offline.add_argument('--offline', dest='offline', default=False, action='store_true',
                             help="Don't query the galaxy API when creating roles")

        default_roles_path = C.config.get_configuration_definition('DEFAULT_ROLES_PATH').get('default', '')
        roles_path = opt_help.argparse.ArgumentParser(add_help=False)
        roles_path.add_argument('-p', '--roles-path', dest='roles_path', type=opt_help.unfrack_path(pathsep=True),
                                default=C.DEFAULT_ROLES_PATH, action=opt_help.PrependListAction,
                                help='The path to the directory containing your roles. The default is the first writable one'
                                     'configured via DEFAULT_ROLES_PATH: %s ' % default_roles_path)

        force = opt_help.argparse.ArgumentParser(add_help=False)
        force.add_argument('-f', '--force', dest='force', action='store_true', default=False,
                           help='Force overwriting an existing role or collection')

        # Add sub parser for the Galaxy role type (role or collection)
        type_parser = self.parser.add_subparsers(metavar='TYPE', dest='type')
        type_parser.required = True

        # Define the actions for the collection object type
        collection = type_parser.add_parser('collection',
                                            parents=[common],
                                            help='Manage an Ansible Galaxy collection.')

        collection_parser = collection.add_subparsers(metavar='ACTION', dest='collection')
        collection_parser.required = True

        build_parser = collection_parser.add_parser(
            'build', help='Build an Ansible collection artifact that can be published to Ansible Galaxy.',
            parents=[common, force])
        build_parser.set_defaults(func=self.execute_build)
        build_parser.add_argument(
            'args', metavar='collection', nargs='*', default=('./',),
            help='Path to the collection(s) directory to build. This should be the directory that contains the '
                 'galaxy.yml file. The default is the current working directory.')

        build_parser.add_argument(
            '--output-path', dest='output_path', default='./',
            help='The path in which the collection is built to. The default is the current working directory.')

        self.add_init_parser(collection_parser, [common, force])

        cinstall_parser = collection_parser.add_parser('install', help='Install collection from Ansible Galaxy',
                                                       parents=[force, common])
        cinstall_parser.set_defaults(func=self.execute_install)
        cinstall_parser.add_argument('args', metavar='collection_name', nargs='*',
                                     help='The collection(s) name or path/url to a tar.gz collection artifact. This '
                                          'is mutually exclusive with --requirements-file.')
        cinstall_parser.add_argument('-p', '--collections-path', dest='collections_path', required=True,
                                     help='The path to the directory containing your collections.')
        cinstall_parser.add_argument('-i', '--ignore-errors', dest='ignore_errors', action='store_true', default=False,
                                     help='Ignore errors during installation and continue with the next specified '
                                          'collection. This will not ignore dependency conflict errors.')
        cinstall_parser.add_argument('-r', '--requirements-file', dest='requirements',
                                     help='A file containing a list of collections to be installed.')

        cinstall_exclusive = cinstall_parser.add_mutually_exclusive_group()
        cinstall_exclusive.add_argument('-n', '--no-deps', dest='no_deps', action='store_true', default=False,
                                        help="Don't download collections listed as dependencies")
        cinstall_exclusive.add_argument('--force-with-deps', dest='force_with_deps', action='store_true', default=False,
                                        help="Force overwriting an existing collection and its dependencies")

        publish_parser = collection_parser.add_parser(
            'publish', help='Publish a collection artifact to Ansible Galaxy.',
            parents=[common])
        publish_parser.set_defaults(func=self.execute_publish)
        publish_parser.add_argument(
            'args', metavar='collection_path', help='The path to the collection tarball to publish.')
        publish_parser.add_argument(
            '--api-key', dest='api_key',
            help='The Ansible Galaxy API key which can be found at https://galaxy.ansible.com/me/preferences. '
                 'You can also use ansible-galaxy login to retrieve this key.')
        publish_parser.add_argument(
            '--no-wait', dest='wait', action='store_false', default=True,
            help="Don't wait for import validation results.")

        # Define the actions for the role object type
        role = type_parser.add_parser('role',
                                      parents=[common],
                                      help='Manage an Ansible Galaxy role.')
        role_parser = role.add_subparsers(metavar='ACTION', dest='role')
        role_parser.required = True

        delete_parser = role_parser.add_parser('delete', parents=[user_repo, common],
                                               help='Removes the role from Galaxy. It does not remove or alter the actual GitHub repository.')
        delete_parser.set_defaults(func=self.execute_delete)

        import_parser = role_parser.add_parser('import', help='Import a role', parents=[user_repo, common])
        import_parser.set_defaults(func=self.execute_import)
        import_parser.add_argument('--no-wait', dest='wait', action='store_false', default=True, help="Don't wait for import results.")
        import_parser.add_argument('--branch', dest='reference',
                                   help='The name of a branch to import. Defaults to the repository\'s default branch (usually master)')
        import_parser.add_argument('--role-name', dest='role_name', help='The name the role should have, if different than the repo name')
        import_parser.add_argument('--status', dest='check_status', action='store_true', default=False,
                                   help='Check the status of the most recent import request for given github_user/github_repo.')

        info_parser = role_parser.add_parser('info', help='View more details about a specific role.',
                                             parents=[offline, common, roles_path])
        info_parser.set_defaults(func=self.execute_info)
        info_parser.add_argument('args', nargs='+', help='role', metavar='role_name[,version]')

        rinit_parser = self.add_init_parser(role_parser, [offline, force, common])
        rinit_parser.add_argument('--type',
                                  dest='role_type',
                                  action='store',
                                  default='default',
                                  help="Initialize using an alternate role type. Valid types include: 'container', 'apb' and 'network'.")

        install_parser = role_parser.add_parser('install', help='Install Roles from file(s), URL(s) or tar file(s)',
                                                parents=[force, common, roles_path])
        install_parser.set_defaults(func=self.execute_install)
        install_parser.add_argument('-i', '--ignore-errors', dest='ignore_errors', action='store_true', default=False,
                                    help='Ignore errors and continue with the next specified role.')
        install_parser.add_argument('-r', '--role-file', dest='role_file', help='A file containing a list of roles to be imported')
        install_parser.add_argument('-g', '--keep-scm-meta', dest='keep_scm_meta', action='store_true',
                                    default=False, help='Use tar instead of the scm archive option when packaging the role')
        install_parser.add_argument('args', help='Role name, URL or tar file', metavar='role', nargs='*')
        install_exclusive = install_parser.add_mutually_exclusive_group()
        install_exclusive.add_argument('-n', '--no-deps', dest='no_deps', action='store_true', default=False,
                                       help="Don't download roles listed as dependencies")
        install_exclusive.add_argument('--force-with-deps', dest='force_with_deps', action='store_true', default=False,
                                       help="Force overwriting an existing role and it's dependencies")

        remove_parser = role_parser.add_parser('remove', help='Delete roles from roles_path.', parents=[common, roles_path])
        remove_parser.set_defaults(func=self.execute_remove)
        remove_parser.add_argument('args', help='Role(s)', metavar='role', nargs='+')

        list_parser = role_parser.add_parser('list', help='Show the name and version of each role installed in the roles_path.',
                                             parents=[common, roles_path])
        list_parser.set_defaults(func=self.execute_list)
        list_parser.add_argument('role', help='Role', nargs='?', metavar='role')

        login_parser = role_parser.add_parser('login', parents=[common],
                                              help="Login to api.github.com server in order to use ansible-galaxy role "
                                                   "sub command such as 'import', 'delete', 'publish', and 'setup'")
        login_parser.set_defaults(func=self.execute_login)
        login_parser.add_argument('--github-token', dest='token', default=None,
                                  help='Identify with github token rather than username and password.')

        search_parser = role_parser.add_parser('search', help='Search the Galaxy database by tags, platforms, author and multiple keywords.',
                                               parents=[common])
        search_parser.set_defaults(func=self.execute_search)
        search_parser.add_argument('--platforms', dest='platforms', help='list of OS platforms to filter by')
        search_parser.add_argument('--galaxy-tags', dest='galaxy_tags', help='list of galaxy tags to filter by')
        search_parser.add_argument('--author', dest='author', help='GitHub username')
        search_parser.add_argument('args', help='Search terms', metavar='searchterm', nargs='*')

        setup_parser = role_parser.add_parser('setup', help='Manage the integration between Galaxy and the given source.',
                                              parents=[roles_path, common])
        setup_parser.set_defaults(func=self.execute_setup)
        setup_parser.add_argument('--remove', dest='remove_id', default=None,
                                  help='Remove the integration matching the provided ID value. Use --list to see ID values.')
        setup_parser.add_argument('--list', dest="setup_list", action='store_true', default=False, help='List all of your integrations.')
        setup_parser.add_argument('source', help='Source')
        setup_parser.add_argument('github_user', help='GitHub username')
        setup_parser.add_argument('github_repo', help='GitHub repository')
        setup_parser.add_argument('secret', help='Secret')

    def add_init_parser(self, parser, parents):
        galaxy_type = parser.dest

        obj_name_kwargs = {}
        if galaxy_type == 'collection':
            obj_name_kwargs['type'] = GalaxyCLI._validate_collection_name

        init_parser = parser.add_parser('init',
                                        help='Initialize new {0} with the base structure of a {0}.'.format(galaxy_type),
                                        parents=parents)
        init_parser.set_defaults(func=self.execute_init)

        init_parser.add_argument('--init-path',
                                 dest='init_path',
                                 default='./',
                                 help='The path in which the skeleton {0} will be created. The default is the current working directory.'.format(galaxy_type))
        init_parser.add_argument('--{0}-skeleton'.format(galaxy_type),
                                 dest='{0}_skeleton'.format(galaxy_type),
                                 default=C.GALAXY_ROLE_SKELETON,
                                 help='The path to a {0} skeleton that the new {0} should be based upon.'.format(galaxy_type))
        init_parser.add_argument('{0}_name'.format(galaxy_type),
                                 help='{0} name'.format(galaxy_type.capitalize()),
                                 **obj_name_kwargs)

        return init_parser

    def post_process_args(self, options):
        options = super(GalaxyCLI, self).post_process_args(options)
        display.verbosity = options.verbosity
        return options

    def run(self):

        super(GalaxyCLI, self).run()

        self.galaxy = Galaxy()

        self.api = GalaxyAPI(self.galaxy)
        context.CLIARGS['func']()

    @staticmethod
    def exit_without_ignore(rc=1):
        """
        Exits with the specified return code unless the
        option --ignore-errors was specified
        """
        if not context.CLIARGS['ignore_errors']:
            raise AnsibleError('- you can use --ignore-errors to skip failed roles and finish processing the list.')

    @staticmethod
    def _display_role_info(role_info):

        text = [u"", u"Role: %s" % to_text(role_info['name'])]
        text.append(u"\tdescription: %s" % role_info.get('description', ''))

        for k in sorted(role_info.keys()):

            if k in GalaxyCLI.SKIP_INFO_KEYS:
                continue

            if isinstance(role_info[k], dict):
                text.append(u"\t%s:" % (k))
                for key in sorted(role_info[k].keys()):
                    if key in GalaxyCLI.SKIP_INFO_KEYS:
                        continue
                    text.append(u"\t\t%s: %s" % (key, role_info[k][key]))
            else:
                text.append(u"\t%s: %s" % (k, role_info[k]))

        return u'\n'.join(text)

    @staticmethod
    def _resolve_path(path):
        return os.path.abspath(os.path.expanduser(os.path.expandvars(path)))

    @staticmethod
    def _validate_collection_name(name):
        if is_collection_ref('ansible_collections.{0}'.format(name)):
            return name

        raise AnsibleError("Invalid collection name, must be in the format <namespace>.<collection>")

    @staticmethod
    def _get_skeleton_galaxy_yml(template_path, inject_data):
        with open(to_bytes(template_path, errors='surrogate_or_strict'), 'rb') as template_obj:
            meta_template = to_text(template_obj.read(), errors='surrogate_or_strict')

        galaxy_meta = get_collections_galaxy_meta_info()

        required_config = []
        optional_config = []
        for meta_entry in galaxy_meta:
            config_list = required_config if meta_entry.get('required', False) else optional_config

            value = inject_data.get(meta_entry['key'], None)
            if not value:
                meta_type = meta_entry.get('type', 'str')

                if meta_type == 'str':
                    value = ''
                elif meta_type == 'list':
                    value = []
                elif meta_type == 'dict':
                    value = {}

            meta_entry['value'] = value
            config_list.append(meta_entry)

        link_pattern = re.compile(r"L\(([^)]+),\s+([^)]+)\)")
        const_pattern = re.compile(r"C\(([^)]+)\)")

        def comment_ify(v):
            if isinstance(v, list):
                v = ". ".join([l.rstrip('.') for l in v])

            v = link_pattern.sub(r"\1 <\2>", v)
            v = const_pattern.sub(r"'\1'", v)

            return textwrap.fill(v, width=117, initial_indent="# ", subsequent_indent="# ", break_on_hyphens=False)

        def to_yaml(v):
            return yaml.safe_dump(v, default_flow_style=False).rstrip()

        env = Environment(loader=BaseLoader)
        env.filters['comment_ify'] = comment_ify
        env.filters['to_yaml'] = to_yaml

        template = env.from_string(meta_template)
        meta_value = template.render({'required_config': required_config, 'optional_config': optional_config})

        return meta_value

############################
# execute actions
############################

    def execute_role(self):
        """
        Perform the action on an Ansible Galaxy role. Must be combined with a further action like delete/install/init
        as listed below.
        """
        # To satisfy doc build
        pass

    def execute_collection(self):
        """
        Perform the action on an Ansible Galaxy collection. Must be combined with a further action like init/install as
        listed below.
        """
        # To satisfy doc build
        pass

    def execute_build(self):
        """
        Build an Ansible Galaxy collection artifact that can be stored in a central repository like Ansible Galaxy.
        By default, this command builds from the current working directory. You can optionally pass in the
        collection input path (where the ``galaxy.yml`` file is).
        """
        force = context.CLIARGS['force']
        output_path = GalaxyCLI._resolve_path(context.CLIARGS['output_path'])
        b_output_path = to_bytes(output_path, errors='surrogate_or_strict')

        if not os.path.exists(b_output_path):
            os.makedirs(b_output_path)
        elif os.path.isfile(b_output_path):
            raise AnsibleError("- the output collection directory %s is a file - aborting" % to_native(output_path))

        for collection_path in context.CLIARGS['args']:
            collection_path = GalaxyCLI._resolve_path(collection_path)
            build_collection(collection_path, output_path, force)

    def execute_init(self):
        """
        Creates the skeleton framework of a role or collection that complies with the Galaxy metadata format.
        Requires a role or collection name. The collection name must be in the format ``<namespace>.<collection>``.
        """

        galaxy_type = context.CLIARGS['type']
        init_path = context.CLIARGS['init_path']
        force = context.CLIARGS['force']
        obj_skeleton = context.CLIARGS['{0}_skeleton'.format(galaxy_type)]

        obj_name = context.CLIARGS['{0}_name'.format(galaxy_type)]

        inject_data = dict(
            description='your {0} description'.format(galaxy_type),
            ansible_plugin_list_dir=get_versioned_doclink('plugins/plugins.html'),
        )
        if galaxy_type == 'role':
            inject_data.update(dict(
                author='your name',
                company='your company (optional)',
                license='license (GPL-2.0-or-later, MIT, etc)',
                role_name=obj_name,
                role_type=context.CLIARGS['role_type'],
                issue_tracker_url='http://example.com/issue/tracker',
                repository_url='http://example.com/repository',
                documentation_url='http://docs.example.com',
                homepage_url='http://example.com',
                min_ansible_version=ansible_version[:3],  # x.y
            ))

            obj_path = os.path.join(init_path, obj_name)
        elif galaxy_type == 'collection':
            namespace, collection_name = obj_name.split('.', 1)

            inject_data.update(dict(
                namespace=namespace,
                collection_name=collection_name,
                version='1.0.0',
                readme='README.md',
                authors=['your name <example@domain.com>'],
                license=['GPL-2.0-or-later'],
                repository='http://example.com/repository',
                documentation='http://docs.example.com',
                homepage='http://example.com',
                issues='http://example.com/issue/tracker',
            ))

            obj_path = os.path.join(init_path, namespace, collection_name)

        b_obj_path = to_bytes(obj_path, errors='surrogate_or_strict')

        if os.path.exists(b_obj_path):
            if os.path.isfile(obj_path):
                raise AnsibleError("- the path %s already exists, but is a file - aborting" % to_native(obj_path))
            elif not force:
                raise AnsibleError("- the directory %s already exists. "
                                   "You can use --force to re-initialize this directory,\n"
                                   "however it will reset any main.yml files that may have\n"
                                   "been modified there already." % to_native(obj_path))

        if obj_skeleton is not None:
            own_skeleton = False
            skeleton_ignore_expressions = C.GALAXY_ROLE_SKELETON_IGNORE
        else:
            own_skeleton = True
            obj_skeleton = self.galaxy.default_role_skeleton_path
            skeleton_ignore_expressions = ['^.*/.git_keep$']

        obj_skeleton = os.path.expanduser(obj_skeleton)
        skeleton_ignore_re = [re.compile(x) for x in skeleton_ignore_expressions]

        if not os.path.exists(obj_skeleton):
            raise AnsibleError("- the skeleton path '{0}' does not exist, cannot init {1}".format(
                to_native(obj_skeleton), galaxy_type)
            )

        template_env = Environment(loader=FileSystemLoader(obj_skeleton))

        # create role directory
        if not os.path.exists(b_obj_path):
            os.makedirs(b_obj_path)

        for root, dirs, files in os.walk(obj_skeleton, topdown=True):
            rel_root = os.path.relpath(root, obj_skeleton)
            rel_dirs = rel_root.split(os.sep)
            rel_root_dir = rel_dirs[0]
            if galaxy_type == 'collection':
                # A collection can contain templates in playbooks/*/templates and roles/*/templates
                in_templates_dir = rel_root_dir in ['playbooks', 'roles'] and 'templates' in rel_dirs
            else:
                in_templates_dir = rel_root_dir == 'templates'

            dirs[:] = [d for d in dirs if not any(r.match(d) for r in skeleton_ignore_re)]

            for f in files:
                filename, ext = os.path.splitext(f)

                if any(r.match(os.path.join(rel_root, f)) for r in skeleton_ignore_re):
                    continue
                elif galaxy_type == 'collection' and own_skeleton and rel_root == '.' and f == 'galaxy.yml.j2':
                    # Special use case for galaxy.yml.j2 in our own default collection skeleton. We build the options
                    # dynamically which requires special options to be set.

                    # The templated data's keys must match the key name but the inject data contains collection_name
                    # instead of name. We just make a copy and change the key back to name for this file.
                    template_data = inject_data.copy()
                    template_data['name'] = template_data.pop('collection_name')

                    meta_value = GalaxyCLI._get_skeleton_galaxy_yml(os.path.join(root, rel_root, f), template_data)
                    b_dest_file = to_bytes(os.path.join(obj_path, rel_root, filename), errors='surrogate_or_strict')
                    with open(b_dest_file, 'wb') as galaxy_obj:
                        galaxy_obj.write(to_bytes(meta_value, errors='surrogate_or_strict'))
                elif ext == ".j2" and not in_templates_dir:
                    src_template = os.path.join(rel_root, f)
                    dest_file = os.path.join(obj_path, rel_root, filename)
                    template_env.get_template(src_template).stream(inject_data).dump(dest_file, encoding='utf-8')
                else:
                    f_rel_path = os.path.relpath(os.path.join(root, f), obj_skeleton)
                    shutil.copyfile(os.path.join(root, f), os.path.join(obj_path, f_rel_path))

            for d in dirs:
                b_dir_path = to_bytes(os.path.join(obj_path, rel_root, d), errors='surrogate_or_strict')
                if not os.path.exists(b_dir_path):
                    os.makedirs(b_dir_path)

        display.display("- %s %s was created successfully" % (galaxy_type.title(), obj_name))

    def execute_info(self):
        """
        prints out detailed information about an installed role as well as info available from the galaxy API.
        """

        roles_path = context.CLIARGS['roles_path']

        data = ''
        for role in context.CLIARGS['args']:

            role_info = {'path': roles_path}
            gr = GalaxyRole(self.galaxy, role)

            install_info = gr.install_info
            if install_info:
                if 'version' in install_info:
                    install_info['installed_version'] = install_info['version']
                    del install_info['version']
                role_info.update(install_info)

            remote_data = False
            if not context.CLIARGS['offline']:
                remote_data = self.api.lookup_role_by_name(role, False)

            if remote_data:
                role_info.update(remote_data)

            if gr.metadata:
                role_info.update(gr.metadata)

            req = RoleRequirement()
            role_spec = req.role_yaml_parse({'role': role})
            if role_spec:
                role_info.update(role_spec)

            data = self._display_role_info(role_info)
            # FIXME: This is broken in both 1.9 and 2.0 as
            # _display_role_info() always returns something
            if not data:
                data = u"\n- the role %s was not found" % role

        self.pager(data)

    def execute_install(self):
        """
        Install one or more roles(``ansible-galaxy role install``), or one or more collections(``ansible-galaxy collection install``).
        You can pass in a list (roles or collections) or use the file
        option listed below (these are mutually exclusive). If you pass in a list, it
        can be a name (which will be downloaded via the galaxy API and github), or it can be a local tar archive file.
        """
        if context.CLIARGS['type'] == 'collection':
            collections = context.CLIARGS['args']
            force = context.CLIARGS['force']
            output_path = context.CLIARGS['collections_path']
            # TODO: use a list of server that have been configured in ~/.ansible_galaxy
            servers = [context.CLIARGS['api_server']]
            ignore_certs = context.CLIARGS['ignore_certs']
            ignore_errors = context.CLIARGS['ignore_errors']
            requirements_file = context.CLIARGS['requirements']
            no_deps = context.CLIARGS['no_deps']
            force_deps = context.CLIARGS['force_with_deps']

            if collections and requirements_file:
                raise AnsibleError("The positional collection_name arg and --requirements-file are mutually exclusive.")
            elif not collections and not requirements_file:
                raise AnsibleError("You must specify a collection name or a requirements file.")

            if requirements_file:
                requirements_file = GalaxyCLI._resolve_path(requirements_file)
                collection_requirements = parse_collections_requirements_file(requirements_file)
            else:
                collection_requirements = []
                for collection_input in collections:
                    name, dummy, requirement = collection_input.partition(':')
                    collection_requirements.append((name, requirement or '*', None))

            output_path = GalaxyCLI._resolve_path(output_path)
            collections_path = C.COLLECTIONS_PATHS

            if len([p for p in collections_path if p.startswith(output_path)]) == 0:
                display.warning("The specified collections path '%s' is not part of the configured Ansible "
                                "collections paths '%s'. The installed collection won't be picked up in an Ansible "
                                "run." % (to_text(output_path), to_text(":".join(collections_path))))

            if os.path.split(output_path)[1] != 'ansible_collections':
                output_path = os.path.join(output_path, 'ansible_collections')

            b_output_path = to_bytes(output_path, errors='surrogate_or_strict')
            if not os.path.exists(b_output_path):
                os.makedirs(b_output_path)

            install_collections(collection_requirements, output_path, servers, (not ignore_certs), ignore_errors,
                                no_deps, force, force_deps)

            return 0

        role_file = context.CLIARGS['role_file']

        if not context.CLIARGS['args'] and role_file is None:
            # the user needs to specify one of either --role-file or specify a single user/role name
            raise AnsibleOptionsError("- you must specify a user/role name or a roles file")

        no_deps = context.CLIARGS['no_deps']
        force_deps = context.CLIARGS['force_with_deps']

        force = context.CLIARGS['force'] or force_deps

        roles_left = []
        if role_file:
            try:
                f = open(role_file, 'r')
                if role_file.endswith('.yaml') or role_file.endswith('.yml'):
                    try:
                        required_roles = yaml.safe_load(f.read())
                    except Exception as e:
                        raise AnsibleError(
                            "Unable to load data from the requirements file (%s): %s" % (role_file, to_native(e))
                        )

                    if required_roles is None:
                        raise AnsibleError("No roles found in file: %s" % role_file)

                    for role in required_roles:
                        if "include" not in role:
                            role = RoleRequirement.role_yaml_parse(role)
                            display.vvv("found role %s in yaml file" % str(role))
                            if "name" not in role and "scm" not in role:
                                raise AnsibleError("Must specify name or src for role")
                            roles_left.append(GalaxyRole(self.galaxy, **role))
                        else:
                            with open(role["include"]) as f_include:
                                try:
                                    roles_left += [
                                        GalaxyRole(self.galaxy, **r) for r in
                                        (RoleRequirement.role_yaml_parse(i) for i in yaml.safe_load(f_include))
                                    ]
                                except Exception as e:
                                    msg = "Unable to load data from the include requirements file: %s %s"
                                    raise AnsibleError(msg % (role_file, e))
                else:
                    raise AnsibleError("Invalid role requirements file")
                f.close()
            except (IOError, OSError) as e:
                raise AnsibleError('Unable to open %s: %s' % (role_file, to_native(e)))
        else:
            # roles were specified directly, so we'll just go out grab them
            # (and their dependencies, unless the user doesn't want us to).
            for rname in context.CLIARGS['args']:
                role = RoleRequirement.role_yaml_parse(rname.strip())
                roles_left.append(GalaxyRole(self.galaxy, **role))

        for role in roles_left:
            # only process roles in roles files when names matches if given
            if role_file and context.CLIARGS['args'] and role.name not in context.CLIARGS['args']:
                display.vvv('Skipping role %s' % role.name)
                continue

            display.vvv('Processing role %s ' % role.name)

            # query the galaxy API for the role data

            if role.install_info is not None:
                if role.install_info['version'] != role.version or force:
                    if force:
                        display.display('- changing role %s from %s to %s' %
                                        (role.name, role.install_info['version'], role.version or "unspecified"))
                        role.remove()
                    else:
                        display.warning('- %s (%s) is already installed - use --force to change version to %s' %
                                        (role.name, role.install_info['version'], role.version or "unspecified"))
                        continue
                else:
                    if not force:
                        display.display('- %s is already installed, skipping.' % str(role))
                        continue

            try:
                installed = role.install()
            except AnsibleError as e:
                display.warning(u"- %s was NOT installed successfully: %s " % (role.name, to_text(e)))
                self.exit_without_ignore()
                continue

            # install dependencies, if we want them
            if not no_deps and installed:
                if not role.metadata:
                    display.warning("Meta file %s is empty. Skipping dependencies." % role.path)
                else:
                    role_dependencies = role.metadata.get('dependencies') or []
                    for dep in role_dependencies:
                        display.debug('Installing dep %s' % dep)
                        dep_req = RoleRequirement()
                        dep_info = dep_req.role_yaml_parse(dep)
                        dep_role = GalaxyRole(self.galaxy, **dep_info)
                        if '.' not in dep_role.name and '.' not in dep_role.src and dep_role.scm is None:
                            # we know we can skip this, as it's not going to
                            # be found on galaxy.ansible.com
                            continue
                        if dep_role.install_info is None:
                            if dep_role not in roles_left:
                                display.display('- adding dependency: %s' % to_text(dep_role))
                                roles_left.append(dep_role)
                            else:
                                display.display('- dependency %s already pending installation.' % dep_role.name)
                        else:
                            if dep_role.install_info['version'] != dep_role.version:
                                if force_deps:
                                    display.display('- changing dependant role %s from %s to %s' %
                                                    (dep_role.name, dep_role.install_info['version'], dep_role.version or "unspecified"))
                                    dep_role.remove()
                                    roles_left.append(dep_role)
                                else:
                                    display.warning('- dependency %s (%s) from role %s differs from already installed version (%s), skipping' %
                                                    (to_text(dep_role), dep_role.version, role.name, dep_role.install_info['version']))
                            else:
                                if force_deps:
                                    roles_left.append(dep_role)
                                else:
                                    display.display('- dependency %s is already installed, skipping.' % dep_role.name)

            if not installed:
                display.warning("- %s was NOT installed successfully." % role.name)
                self.exit_without_ignore()

        return 0

    def execute_remove(self):
        """
        removes the list of roles passed as arguments from the local system.
        """

        if not context.CLIARGS['args']:
            raise AnsibleOptionsError('- you must specify at least one role to remove.')

        for role_name in context.CLIARGS['args']:
            role = GalaxyRole(self.galaxy, role_name)
            try:
                if role.remove():
                    display.display('- successfully removed %s' % role_name)
                else:
                    display.display('- %s is not installed, skipping.' % role_name)
            except Exception as e:
                raise AnsibleError("Failed to remove role %s: %s" % (role_name, to_native(e)))

        return 0

    def execute_list(self):
        """
        lists the roles installed on the local system or matches a single role passed as an argument.
        """

        def _display_role(gr):
            install_info = gr.install_info
            version = None
            if install_info:
                version = install_info.get("version", None)
            if not version:
                version = "(unknown version)"
            display.display("- %s, %s" % (gr.name, version))

        if context.CLIARGS['role']:
            # show the requested role, if it exists
            name = context.CLIARGS['role']
            gr = GalaxyRole(self.galaxy, name)
            if gr.metadata:
                display.display('# %s' % os.path.dirname(gr.path))
                _display_role(gr)
            else:
                display.display("- the role %s was not found" % name)
        else:
            # show all valid roles in the roles_path directory
            roles_path = context.CLIARGS['roles_path']
            path_found = False
            warnings = []
            for path in roles_path:
                role_path = os.path.expanduser(path)
                if not os.path.exists(role_path):
                    warnings.append("- the configured path %s does not exist." % role_path)
                    continue
                elif not os.path.isdir(role_path):
                    warnings.append("- the configured path %s, exists, but it is not a directory." % role_path)
                    continue
                display.display('# %s' % role_path)
                path_files = os.listdir(role_path)
                path_found = True
                for path_file in path_files:
                    gr = GalaxyRole(self.galaxy, path_file, path=path)
                    if gr.metadata:
                        _display_role(gr)
            for w in warnings:
                display.warning(w)
            if not path_found:
                raise AnsibleOptionsError("- None of the provided paths was usable. Please specify a valid path with --roles-path")
        return 0

    def execute_publish(self):
        """
        Publish a collection into Ansible Galaxy. Requires the path to the collection tarball to publish.
        """
        api_key = context.CLIARGS['api_key'] or GalaxyToken().get()
        api_server = context.CLIARGS['api_server']
        collection_path = GalaxyCLI._resolve_path(context.CLIARGS['args'])
        ignore_certs = context.CLIARGS['ignore_certs']
        wait = context.CLIARGS['wait']

        publish_collection(collection_path, api_server, api_key, ignore_certs, wait)

    def execute_search(self):
        ''' searches for roles on the Ansible Galaxy server'''
        page_size = 1000
        search = None

        if context.CLIARGS['args']:
            search = '+'.join(context.CLIARGS['args'])

        if not search and not context.CLIARGS['platforms'] and not context.CLIARGS['galaxy_tags'] and not context.CLIARGS['author']:
            raise AnsibleError("Invalid query. At least one search term, platform, galaxy tag or author must be provided.")

        response = self.api.search_roles(search, platforms=context.CLIARGS['platforms'],
                                         tags=context.CLIARGS['galaxy_tags'], author=context.CLIARGS['author'], page_size=page_size)

        if response['count'] == 0:
            display.display("No roles match your search.", color=C.COLOR_ERROR)
            return True

        data = [u'']

        if response['count'] > page_size:
            data.append(u"Found %d roles matching your search. Showing first %s." % (response['count'], page_size))
        else:
            data.append(u"Found %d roles matching your search:" % response['count'])

        max_len = []
        for role in response['results']:
            max_len.append(len(role['username'] + '.' + role['name']))
        name_len = max(max_len)
        format_str = u" %%-%ds %%s" % name_len
        data.append(u'')
        data.append(format_str % (u"Name", u"Description"))
        data.append(format_str % (u"----", u"-----------"))
        for role in response['results']:
            data.append(format_str % (u'%s.%s' % (role['username'], role['name']), role['description']))

        data = u'\n'.join(data)
        self.pager(data)

        return True

    def execute_login(self):
        """
        verify user's identify via Github and retrieve an auth token from Ansible Galaxy.
        """
        # Authenticate with github and retrieve a token
        if context.CLIARGS['token'] is None:
            if C.GALAXY_TOKEN:
                github_token = C.GALAXY_TOKEN
            else:
                login = GalaxyLogin(self.galaxy)
                github_token = login.create_github_token()
        else:
            github_token = context.CLIARGS['token']

        galaxy_response = self.api.authenticate(github_token)

        if context.CLIARGS['token'] is None and C.GALAXY_TOKEN is None:
            # Remove the token we created
            login.remove_github_token()

        # Store the Galaxy token
        token = GalaxyToken()
        token.set(galaxy_response['token'])

        display.display("Successfully logged into Galaxy as %s" % galaxy_response['username'])
        return 0

    def execute_import(self):
        """ used to import a role into Ansible Galaxy """

        colors = {
            'INFO': 'normal',
            'WARNING': C.COLOR_WARN,
            'ERROR': C.COLOR_ERROR,
            'SUCCESS': C.COLOR_OK,
            'FAILED': C.COLOR_ERROR,
        }

        github_user = to_text(context.CLIARGS['github_user'], errors='surrogate_or_strict')
        github_repo = to_text(context.CLIARGS['github_repo'], errors='surrogate_or_strict')

        if context.CLIARGS['check_status']:
            task = self.api.get_import_task(github_user=github_user, github_repo=github_repo)
        else:
            # Submit an import request
            task = self.api.create_import_task(github_user, github_repo,
                                               reference=context.CLIARGS['reference'],
                                               role_name=context.CLIARGS['role_name'])

            if len(task) > 1:
                # found multiple roles associated with github_user/github_repo
                display.display("WARNING: More than one Galaxy role associated with Github repo %s/%s." % (github_user, github_repo),
                                color='yellow')
                display.display("The following Galaxy roles are being updated:" + u'\n', color=C.COLOR_CHANGED)
                for t in task:
                    display.display('%s.%s' % (t['summary_fields']['role']['namespace'], t['summary_fields']['role']['name']), color=C.COLOR_CHANGED)
                display.display(u'\nTo properly namespace this role, remove each of the above and re-import %s/%s from scratch' % (github_user, github_repo),
                                color=C.COLOR_CHANGED)
                return 0
            # found a single role as expected
            display.display("Successfully submitted import request %d" % task[0]['id'])
            if not context.CLIARGS['wait']:
                display.display("Role name: %s" % task[0]['summary_fields']['role']['name'])
                display.display("Repo: %s/%s" % (task[0]['github_user'], task[0]['github_repo']))

        if context.CLIARGS['check_status'] or context.CLIARGS['wait']:
            # Get the status of the import
            msg_list = []
            finished = False
            while not finished:
                task = self.api.get_import_task(task_id=task[0]['id'])
                for msg in task[0]['summary_fields']['task_messages']:
                    if msg['id'] not in msg_list:
                        display.display(msg['message_text'], color=colors[msg['message_type']])
                        msg_list.append(msg['id'])
                if task[0]['state'] in ['SUCCESS', 'FAILED']:
                    finished = True
                else:
                    time.sleep(10)

        return 0

    def execute_setup(self):
        """ Setup an integration from Github or Travis for Ansible Galaxy roles"""

        if context.CLIARGS['setup_list']:
            # List existing integration secrets
            secrets = self.api.list_secrets()
            if len(secrets) == 0:
                # None found
                display.display("No integrations found.")
                return 0
            display.display(u'\n' + "ID         Source     Repo", color=C.COLOR_OK)
            display.display("---------- ---------- ----------", color=C.COLOR_OK)
            for secret in secrets:
                display.display("%-10s %-10s %s/%s" % (secret['id'], secret['source'], secret['github_user'],
                                                       secret['github_repo']), color=C.COLOR_OK)
            return 0

        if context.CLIARGS['remove_id']:
            # Remove a secret
            self.api.remove_secret(context.CLIARGS['remove_id'])
            display.display("Secret removed. Integrations using this secret will not longer work.", color=C.COLOR_OK)
            return 0

        source = context.CLIARGS['source']
        github_user = context.CLIARGS['github_user']
        github_repo = context.CLIARGS['github_repo']
        secret = context.CLIARGS['secret']

        resp = self.api.add_secret(source, github_user, github_repo, secret)
        display.display("Added integration for %s %s/%s" % (resp['source'], resp['github_user'], resp['github_repo']))

        return 0

    def execute_delete(self):
        """ Delete a role from Ansible Galaxy. """

        github_user = context.CLIARGS['github_user']
        github_repo = context.CLIARGS['github_repo']
        resp = self.api.delete_role(github_user, github_repo)

        if len(resp['deleted_roles']) > 1:
            display.display("Deleted the following roles:")
            display.display("ID     User            Name")
            display.display("------ --------------- ----------")
            for role in resp['deleted_roles']:
                display.display("%-8s %-15s %s" % (role.id, role.namespace, role.name))

        display.display(resp['status'])

        return True
