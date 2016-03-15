########################################################################
#
# (C) 2013, James Cammarata <jcammarata@ansible.com>
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.
#
########################################################################

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os.path
import sys
import yaml
import time

from collections import defaultdict
from jinja2 import Environment

import ansible.constants as C
from ansible.cli import CLI
from ansible.errors import AnsibleError, AnsibleOptionsError
from ansible.galaxy import Galaxy
from ansible.galaxy.api import GalaxyAPI
from ansible.galaxy.role import GalaxyRole
from ansible.galaxy.login import GalaxyLogin
from ansible.galaxy.token import GalaxyToken
from ansible.playbook.role.requirement import RoleRequirement
from ansible.utils.unicode import to_unicode

try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display
    display = Display()

class GalaxyCLI(CLI):

    SKIP_INFO_KEYS = ("name", "description", "readme_html", "related", "summary_fields", "average_aw_composite", "average_aw_score", "url" )
    VALID_ACTIONS = ("delete", "import", "info", "init", "install", "list", "login", "remove", "search", "setup")
    
    def __init__(self, args):
        self.api = None
        self.galaxy = None
        super(GalaxyCLI, self).__init__(args)

    def parse(self):
        ''' create an options parser for bin/ansible '''

        self.parser = CLI.base_parser(
            usage = "usage: %%prog [%s] [--help] [options] ..." % "|".join(self.VALID_ACTIONS),
            epilog = "\nSee '%s <command> --help' for more information on a specific command.\n\n" % os.path.basename(sys.argv[0])
        )

        self.set_action()

        # options specific to actions
        if self.action == "delete":
            self.parser.set_usage("usage: %prog delete [options] github_user github_repo")
        elif self.action == "import":
            self.parser.set_usage("usage: %prog import [options] github_user github_repo")
            self.parser.add_option('--no-wait', dest='wait', action='store_false', default=True,
                help='Don\'t wait for import results.')
            self.parser.add_option('--branch', dest='reference',
                help='The name of a branch to import. Defaults to the repository\'s default branch (usually master)')
            self.parser.add_option('--status', dest='check_status', action='store_true', default=False,
                help='Check the status of the most recent import request for given github_user/github_repo.')
        elif self.action == "info":
            self.parser.set_usage("usage: %prog info [options] role_name[,version]")
        elif self.action == "init":
            self.parser.set_usage("usage: %prog init [options] role_name")
            self.parser.add_option('-p', '--init-path', dest='init_path', default="./",
                help='The path in which the skeleton role will be created. The default is the current working directory.')
            self.parser.add_option(
                '--offline', dest='offline', default=False, action='store_true',
                help="Don't query the galaxy API when creating roles")
        elif self.action == "install":
            self.parser.set_usage("usage: %prog install [options] [-r FILE | role_name(s)[,version] | scm+role_repo_url[,version] | tar_file(s)]")
            self.parser.add_option('-i', '--ignore-errors', dest='ignore_errors', action='store_true', default=False,
                help='Ignore errors and continue with the next specified role.')
            self.parser.add_option('-n', '--no-deps', dest='no_deps', action='store_true', default=False,
                help='Don\'t download roles listed as dependencies')
            self.parser.add_option('-r', '--role-file', dest='role_file',
                help='A file containing a list of roles to be imported')
        elif self.action == "remove":
            self.parser.set_usage("usage: %prog remove role1 role2 ...")
        elif self.action == "list":
            self.parser.set_usage("usage: %prog list [role_name]")
        elif self.action == "login":
            self.parser.set_usage("usage: %prog login [options]")
            self.parser.add_option('--github-token', dest='token', default=None,
                help='Identify with github token rather than username and password.')
        elif self.action == "search":
            self.parser.add_option('--platforms', dest='platforms',
                help='list of OS platforms to filter by')
            self.parser.add_option('--galaxy-tags', dest='tags',
                help='list of galaxy tags to filter by')
            self.parser.add_option('--author', dest='author',
                help='GitHub username')
            self.parser.set_usage("usage: %prog search [searchterm1 searchterm2] [--galaxy-tags galaxy_tag1,galaxy_tag2] [--platforms platform1,platform2] [--author username]")
        elif self.action == "setup":
            self.parser.set_usage("usage: %prog setup [options] source github_user github_repo secret")
            self.parser.add_option('--remove', dest='remove_id', default=None,
                help='Remove the integration matching the provided ID value. Use --list to see ID values.')
            self.parser.add_option('--list', dest="setup_list", action='store_true', default=False,
                help='List all of your integrations.')

        # options that apply to more than one action
        if not self.action in ("delete","import","init","login","setup"):
            self.parser.add_option('-p', '--roles-path', dest='roles_path', default=C.DEFAULT_ROLES_PATH,
                help='The path to the directory containing your roles. '
                     'The default is the roles_path configured in your '
                     'ansible.cfg file (/etc/ansible/roles if not configured)')

        if self.action in ("import","info","init","install","login","search","setup","delete"):
            self.parser.add_option('-s', '--server', dest='api_server', default=C.GALAXY_SERVER,
                help='The API server destination')
            self.parser.add_option('-c', '--ignore-certs', action='store_true', dest='ignore_certs', default=False,
                help='Ignore SSL certificate validation errors.')

        if self.action in ("init","install"):
            self.parser.add_option('-f', '--force', dest='force', action='store_true', default=False,
                help='Force overwriting an existing role')

        self.options, self.args =self.parser.parse_args()
        display.verbosity = self.options.verbosity
        self.galaxy = Galaxy(self.options)

        return True

    def run(self):
        
        super(GalaxyCLI, self).run()

        # if not offline, get connect to galaxy api
        if self.action in ("import","info","install","search","login","setup","delete") or \
            (self.action == 'init' and not self.options.offline):
            self.api = GalaxyAPI(self.galaxy)

        self.execute()

    def exit_without_ignore(self, rc=1):
        """
        Exits with the specified return code unless the
        option --ignore-errors was specified
        """
        if not self.get_opt("ignore_errors", False):
            raise AnsibleError('- you can use --ignore-errors to skip failed roles and finish processing the list.')

    def _display_role_info(self, role_info):

        text = [u"", u"Role: %s" % to_unicode(role_info['name'])]
        text.append(u"\tdescription: %s" % role_info.get('description', ''))

        for k in sorted(role_info.keys()):

            if k in self.SKIP_INFO_KEYS:
                continue

            if isinstance(role_info[k], dict):
                text += "\t%s: \n" % (k)
                text.append(u"\t%s:" % (k))
                for key in sorted(role_info[k].keys()):
                    if key in self.SKIP_INFO_KEYS:
                        continue
                    text.append(u"\t\t%s: %s" % (key, role_info[k][key]))
            else:
                text.append(u"\t%s: %s" % (k, role_info[k]))

        return u'\n'.join(text)

############################
# execute actions
############################

    def execute_init(self):
        """
        Executes the init action, which creates the skeleton framework
        of a role that complies with the galaxy metadata format.
        """

        init_path  = self.get_opt('init_path', './')
        force      = self.get_opt('force', False)
        offline    = self.get_opt('offline', False)

        role_name = self.args.pop(0).strip() if self.args else None
        if not role_name:
            raise AnsibleOptionsError("- no role name specified for init")
        role_path = os.path.join(init_path, role_name)
        if os.path.exists(role_path):
            if os.path.isfile(role_path):
                raise AnsibleError("- the path %s already exists, but is a file - aborting" % role_path)
            elif not force:
                raise AnsibleError("- the directory %s already exists."
                            "you can use --force to re-initialize this directory,\n"
                            "however it will reset any main.yml files that may have\n"
                            "been modified there already." % role_path)

        # create default README.md
        if not os.path.exists(role_path):
            os.makedirs(role_path)
        readme_path = os.path.join(role_path, "README.md")
        f = open(readme_path, "wb")
        f.write(self.galaxy.default_readme)
        f.close()

        # create default .travis.yml
        travis = Environment().from_string(self.galaxy.default_travis).render()
        f = open(os.path.join(role_path, '.travis.yml'), 'w')
        f.write(travis)
        f.close()

        for dir in GalaxyRole.ROLE_DIRS:
            dir_path = os.path.join(init_path, role_name, dir)
            main_yml_path = os.path.join(dir_path, 'main.yml')

            # create the directory if it doesn't exist already
            if not os.path.exists(dir_path):
                os.makedirs(dir_path)

            # now create the main.yml file for that directory
            if dir == "meta":
                # create a skeleton meta/main.yml with a valid galaxy_info
                # datastructure in place, plus with all of the available
                # platforms included (but commented out), the galaxy_tags
                # list, and the dependencies section
                platforms = []
                if not offline and self.api:
                    platforms = self.api.get_list("platforms") or []

                # group the list of platforms from the api based
                # on their names, with the release field being
                # appended to a list of versions
                platform_groups = defaultdict(list)
                for platform in platforms:
                    platform_groups[platform['name']].append(platform['release'])
                    platform_groups[platform['name']].sort()

                inject = dict(
                    author = 'your name',
                    company = 'your company (optional)',
                    license = 'license (GPLv2, CC-BY, etc)',
                    issue_tracker_url = 'http://example.com/issue/tracker',
                    min_ansible_version = '1.2',
                    platforms = platform_groups,
                )
                rendered_meta = Environment().from_string(self.galaxy.default_meta).render(inject)
                f = open(main_yml_path, 'w')
                f.write(rendered_meta)
                f.close()
                pass
            elif dir == "tests":
                # create tests/test.yml
                inject = dict(
                    role_name = role_name
                )
                playbook = Environment().from_string(self.galaxy.default_test).render(inject)
                f = open(os.path.join(dir_path, 'test.yml'), 'w')
                f.write(playbook)
                f.close()

                # create tests/inventory
                f = open(os.path.join(dir_path, 'inventory'), 'w')
                f.write('localhost')
                f.close()
            elif dir not in ('files','templates'):
                # just write a (mostly) empty YAML file for main.yml
                f = open(main_yml_path, 'w')
                f.write('---\n# %s file for %s\n' % (dir,role_name))
                f.close()
        display.display("- %s was created successfully" % role_name)

    def execute_info(self):
        """
        Executes the info action. This action prints out detailed
        information about an installed role as well as info available
        from the galaxy API.
        """

        if len(self.args) == 0:
            # the user needs to specify a role
            raise AnsibleOptionsError("- you must specify a user/role name")

        roles_path = self.get_opt("roles_path")

        data = ''
        for role in self.args:

            role_info = {'path': roles_path}
            gr = GalaxyRole(self.galaxy, role)

            install_info = gr.install_info
            if install_info:
                if 'version' in install_info:
                    install_info['intalled_version'] = install_info['version']
                    del install_info['version']
                role_info.update(install_info)

            remote_data = False
            if self.api:
                remote_data = self.api.lookup_role_by_name(role, False)

            if remote_data:
                role_info.update(remote_data)

            if gr.metadata:
                role_info.update(gr.metadata)

            req = RoleRequirement()
            role_spec= req.role_yaml_parse({'role': role})
            if role_spec:
                role_info.update(role_spec)

            data = self._display_role_info(role_info)
            ### FIXME: This is broken in both 1.9 and 2.0 as
            # _display_role_info() always returns something
            if not data:
                data = u"\n- the role %s was not found" % role

        self.pager(data)

    def execute_install(self):
        """
        Executes the installation action. The args list contains the
        roles to be installed, unless -f was specified. The list of roles
        can be a name (which will be downloaded via the galaxy API and github),
        or it can be a local .tar.gz file.
        """

        role_file  = self.get_opt("role_file", None)

        if len(self.args) == 0 and role_file is None:
            # the user needs to specify one of either --role-file
            # or specify a single user/role name
            raise AnsibleOptionsError("- you must specify a user/role name or a roles file")
        elif len(self.args) == 1 and role_file is not None:
            # using a role file is mutually exclusive of specifying
            # the role name on the command line
            raise AnsibleOptionsError("- please specify a user/role name, or a roles file, but not both")

        no_deps    = self.get_opt("no_deps", False)
        force      = self.get_opt('force', False)

        roles_left = []
        if role_file:
            try:
                f = open(role_file, 'r')
                if role_file.endswith('.yaml') or role_file.endswith('.yml'):
                    try:
                        required_roles =  yaml.safe_load(f.read())
                    except Exception as e:
                        raise AnsibleError("Unable to load data from the requirements file: %s" % role_file)

                    if required_roles is None:
                        raise AnsibleError("No roles found in file: %s" % role_file)

                    for role in required_roles:
                        role = RoleRequirement.role_yaml_parse(role)
                        display.vvv('found role %s in yaml file' % str(role))
                        if 'name' not in role and 'scm' not in role:
                            raise AnsibleError("Must specify name or src for role")
                        roles_left.append(GalaxyRole(self.galaxy, **role))
                else:
                    display.deprecated("going forward only the yaml format will be supported")
                    # roles listed in a file, one per line
                    for rline in f.readlines():
                        if rline.startswith("#") or rline.strip() == '':
                            continue
                        display.debug('found role %s in text file' % str(rline))
                        role = RoleRequirement.role_yaml_parse(rline.strip())
                        roles_left.append(GalaxyRole(self.galaxy, **role))
                f.close()
            except (IOError, OSError) as e:
                display.error('Unable to open %s: %s' % (role_file, str(e)))
        else:
            # roles were specified directly, so we'll just go out grab them
            # (and their dependencies, unless the user doesn't want us to).
            for rname in self.args:
                role = RoleRequirement.role_yaml_parse(rname.strip())
                roles_left.append(GalaxyRole(self.galaxy, **role))

        for role in roles_left:
            display.vvv('Installing role %s ' % role.name)
            # query the galaxy API for the role data

            if role.install_info is not None and not force:
                display.display('- %s is already installed, skipping.' % role.name)
                continue

            try:
                installed = role.install()
            except AnsibleError as e:
                display.warning("- %s was NOT installed successfully: %s " % (role.name, str(e)))
                self.exit_without_ignore()
                continue

            # install dependencies, if we want them
            if not no_deps and installed:
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
                    if dep_role.install_info is None or force:
                        if dep_role not in roles_left:
                            display.display('- adding dependency: %s' % dep_role.name)
                            roles_left.append(dep_role)
                        else:
                            display.display('- dependency %s already pending installation.' % dep_role.name)
                    else:
                        display.display('- dependency %s is already installed, skipping.' % dep_role.name)

            if not installed:
                display.warning("- %s was NOT installed successfully." % role.name)
                self.exit_without_ignore()

        return 0

    def execute_remove(self):
        """
        Executes the remove action. The args list contains the list
        of roles to be removed. This list can contain more than one role.
        """

        if len(self.args) == 0:
            raise AnsibleOptionsError('- you must specify at least one role to remove.')

        for role_name in self.args:
            role = GalaxyRole(self.galaxy, role_name)
            try:
                if role.remove():
                    display.display('- successfully removed %s' % role_name)
                else:
                    display.display('- %s is not installed, skipping.' % role_name)
            except Exception as e:
                raise AnsibleError("Failed to remove role %s: %s" % (role_name, str(e)))

        return 0

    def execute_list(self):
        """
        Executes the list action. The args list can contain zero
        or one role. If one is specified, only that role will be
        shown, otherwise all roles in the specified directory will
        be shown.
        """

        if len(self.args) > 1:
            raise AnsibleOptionsError("- please specify only one role to list, or specify no roles to see a full list")

        if len(self.args) == 1:
            # show only the request role, if it exists
            name = self.args.pop()
            gr = GalaxyRole(self.galaxy, name)
            if gr.metadata:
                install_info = gr.install_info
                version = None
                if install_info:
                    version = install_info.get("version", None)
                if not version:
                    version = "(unknown version)"
                # show some more info about single roles here
                display.display("- %s, %s" % (name, version))
            else:
                display.display("- the role %s was not found" % name)
        else:
            # show all valid roles in the roles_path directory
            roles_path = self.get_opt('roles_path')
            roles_path = os.path.expanduser(roles_path)
            if not os.path.exists(roles_path):
                raise AnsibleOptionsError("- the path %s does not exist. Please specify a valid path with --roles-path" % roles_path)
            elif not os.path.isdir(roles_path):
                raise AnsibleOptionsError("- %s exists, but it is not a directory. Please specify a valid path with --roles-path" % roles_path)
            path_files = os.listdir(roles_path)
            for path_file in path_files:
                gr = GalaxyRole(self.galaxy, path_file)
                if gr.metadata:
                    install_info = gr.install_info
                    version = None
                    if install_info:
                        version = install_info.get("version", None)
                    if not version:
                        version = "(unknown version)"
                    display.display("- %s, %s" % (path_file, version))
        return 0

    def execute_search(self):
        page_size = 1000
        search = None

        if len(self.args):
            terms = []
            for i in range(len(self.args)):
               terms.append(self.args.pop())
            search = '+'.join(terms[::-1])

        if not search and not self.options.platforms and not self.options.tags and not self.options.author:
            raise AnsibleError("Invalid query. At least one search term, platform, galaxy tag or author must be provided.")

        response = self.api.search_roles(search, platforms=self.options.platforms,
            tags=self.options.tags, author=self.options.author, page_size=page_size)

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
        Verify user's identify via Github and retreive an auth token from Galaxy.
        """
        # Authenticate with github and retrieve a token
        if self.options.token is None:
            login = GalaxyLogin(self.galaxy)
            github_token = login.create_github_token()
        else:
            github_token = self.options.token

        galaxy_response = self.api.authenticate(github_token)

        if self.options.token is None:
            # Remove the token we created
            login.remove_github_token()

        # Store the Galaxy token
        token = GalaxyToken()
        token.set(galaxy_response['token'])

        display.display("Succesfully logged into Galaxy as %s" % galaxy_response['username'])
        return 0

    def execute_import(self):
        """
        Import a role into Galaxy
        """

        colors = {
            'INFO':    'normal',
            'WARNING': C.COLOR_WARN,
            'ERROR':   C.COLOR_ERROR,
            'SUCCESS': C.COLOR_OK,
            'FAILED': C.COLOR_ERROR,
        }

        if len(self.args) < 2:
            raise AnsibleError("Expected a github_username and github_repository. Use --help.")

        github_repo = self.args.pop()
        github_user = self.args.pop()

        if self.options.check_status:
            task = self.api.get_import_task(github_user=github_user, github_repo=github_repo)
        else:
            # Submit an import request
            task = self.api.create_import_task(github_user, github_repo, reference=self.options.reference)

            if len(task) > 1:
                # found multiple roles associated with github_user/github_repo
                display.display("WARNING: More than one Galaxy role associated with Github repo %s/%s." % (github_user,github_repo),
                    color='yellow')
                display.display("The following Galaxy roles are being updated:" + u'\n', color=C.COLOR_CHANGED)
                for t in task:
                    display.display('%s.%s' % (t['summary_fields']['role']['namespace'],t['summary_fields']['role']['name']), color=C.COLOR_CHANGED)
                display.display(u'\n' + "To properly namespace this role, remove each of the above and re-import %s/%s from scratch" % (github_user,github_repo), color=C.COLOR_CHANGED)
                return 0
            # found a single role as expected
            display.display("Successfully submitted import request %d" % task[0]['id'])
            if not self.options.wait:
                display.display("Role name: %s" % task[0]['summary_fields']['role']['name'])
                display.display("Repo: %s/%s" % (task[0]['github_user'],task[0]['github_repo']))

        if self.options.check_status or self.options.wait:
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
        """
        Setup an integration from Github or Travis
        """

        if self.options.setup_list:
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
                    secret['github_repo']),color=C.COLOR_OK)
            return 0

        if self.options.remove_id:
            # Remove a secret
            self.api.remove_secret(self.options.remove_id)
            display.display("Secret removed. Integrations using this secret will not longer work.", color=C.COLOR_OK)
            return 0

        if len(self.args) < 4:
            raise AnsibleError("Missing one or more arguments. Expecting: source github_user github_repo secret")
            return 0

        secret = self.args.pop()
        github_repo = self.args.pop()
        github_user = self.args.pop()
        source = self.args.pop()

        resp = self.api.add_secret(source, github_user, github_repo, secret)
        display.display("Added integration for %s %s/%s" % (resp['source'], resp['github_user'], resp['github_repo']))

        return 0

    def execute_delete(self):
        """
        Delete a role from galaxy.ansible.com
        """

        if len(self.args) < 2:
            raise AnsibleError("Missing one or more arguments. Expected: github_user github_repo")

        github_repo = self.args.pop()
        github_user = self.args.pop()
        resp = self.api.delete_role(github_user, github_repo)

        if len(resp['deleted_roles']) > 1:
            display.display("Deleted the following roles:")
            display.display("ID     User            Name")
            display.display("------ --------------- ----------")
            for role in resp['deleted_roles']:
                display.display("%-8s %-15s %s" % (role.id,role.namespace,role.name))

        display.display(resp['status'])

        return True
