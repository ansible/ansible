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

import glob
import os
import os.path
import re
import shutil
import sys
import time
import yaml

from jinja2 import Environment, FileSystemLoader

import ansible.constants as C
from ansible.cli import CLI
from ansible.errors import AnsibleError, AnsibleOptionsError
from ansible.galaxy import Galaxy
from ansible.galaxy.api import GalaxyAPI
from ansible.galaxy.login import GalaxyLogin
from ansible.galaxy.role import GalaxyRole
from ansible.galaxy.token import GalaxyToken
from ansible.module_utils._text import to_text
from ansible.playbook.role.requirement import RoleRequirement
from ansible.utils.path import makedirs_safe

try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display
    display = Display()


class InstallerCLI(CLI):
    '''command to install plugins from roles in Ansible Galaxy *https://galaxy.ansible.com*.'''

    SKIP_INFO_KEYS = ("name", "description", "readme_html", "related", "summary_fields", "average_aw_composite", "average_aw_score", "url")
    VALID_ACTIONS = ("info", "install", "remove", "search", "update")

    def __init__(self, args):
        self.api = None
        self.galaxy = None
        super(InstallerCLI, self).__init__(args)

    def set_action(self):

        super(InstallerCLI, self).set_action()

        # specific to actions
        if self.action == "info":
            self.parser.set_usage("usage: %prog info [options] role_name[,version]")
            self.parser.add_option('--offline', dest='offline', default=False, action='store_true', help="Only give info about locally installed plugins")
        elif self.action == "install":
            self.parser.set_usage("usage: %prog install [options] [-r FILE | role_name(s)[,version] | scm+role_repo_url[,version] | tar_file(s)]")
            self.parser.add_option('-i', '--ignore-errors', dest='ignore_errors', action='store_true', default=False,
                                   help='Ignore errors and continue with the next specified role.')
            self.parser.add_option('-f', '--force', dest='force', action='store_true', default=False, help='Force overwriting an existing role')
            #self.parser.add_option('-n', '--no-deps', dest='no_deps', action='store_true', default=False, help='Don\'t download roles listed as dependencies')
            #self.parser.add_option('-r', '--role-file', dest='role_file', help='A file containing a list of roles to be imported')
        #elif self.action == "list":
        #    self.parser.set_usage("usage: %prog list [role_name]")
        elif self.action == "remove":
            self.parser.set_usage("usage: %prog remove role1 role2 ...")
        elif self.action == "search":
            self.parser.set_usage("usage: %prog search [searchterm1 searchterm2] [--galaxy-tags galaxy_tag1,galaxy_tag2] [--platforms platform1,platform2] "
                                  "[--author username]")
            self.parser.add_option('--platforms', dest='platforms', help='list of OS platforms to filter by')
            self.parser.add_option('--galaxy-tags', dest='galaxy_tags', action="append", default=[],
                                   help='list of galaxy tags to filter by')
            self.parser.add_option('--author', dest='author', help='GitHub username')
        elif self.action == "update":
            pass

    def parse(self):
        ''' create an options parser for bin/ansible '''

        self.parser = CLI.base_parser(
            usage="usage: %%prog [%s] [--help] [options] ..." % "|".join(self.VALID_ACTIONS),
            epilog="\nSee '%s <command> --help' for more information on a specific command.\n\n" % os.path.basename(sys.argv[0])
        )

        # common
        self.parser.add_option('-s', '--server', dest='api_server', default=C.GALAXY_SERVER, help='The API server destination')
        self.parser.add_option('-c', '--ignore-certs', action='store_true', dest='ignore_certs', default=C.GALAXY_IGNORE_CERTS,
                               help='Ignore SSL certificate validation errors.')
        self.parser.add_option('-p', '--roles-path', dest='roles_path', action="callback", callback=CLI.unfrack_paths, default=['/etc/ansible/plugin_pkgs'],
                               help='The path to the directory containing your roles. The default is the roles_path configured in your ansible.cfg'
                                    'file (/etc/ansible/plugin_pkgs if not configured)', type='str')
        self.parser.add_option('-M', '--modules-path', dest='modules_path', action="callback", callback=CLI.unfrack_paths, default=['/etc/ansible/plugins/modules'],
                               help='The path to the directory containing your modules. The default is the modules_path configured in your ansible.cfg'
                                    'file (/etc/ansible/modules if not configured)', type='str')
        self.parser.add_option("-t", "--type", action="store", default='module', dest='type', type='choice',
                               help='Choose which plugin type (defaults to "module")',
                               choices=['cache', 'callback', 'connection', 'inventory', 'lookup', 'module', 'strategy', 'vars'])

        self.set_action()

        super(InstallerCLI, self).parse()

        display.verbosity = self.options.verbosity
        self.galaxy = Galaxy(self.options)

    def run(self):

        super(InstallerCLI, self).run()

        self.api = GalaxyAPI(self.galaxy)
        self.execute()

    def exit_without_ignore(self, rc=1):
        """
        Exits with the specified return code unless the
        option --ignore-errors was specified
        """
        if not self.options.ignore_errors:
            raise AnsibleError('- you can use --ignore-errors to skip failed roles and finish processing the list.')

    def _display_role_info(self, role_info):

        text = [u"", u"Role: %s" % to_text(role_info['name'])]
        text.append(u"\tdescription: %s" % role_info.get('description', ''))

        for k in sorted(role_info.keys()):

            if k in self.SKIP_INFO_KEYS:
                continue

            if isinstance(role_info[k], dict):
                text.append(u"\t%s:" % (k))
                for key in sorted(role_info[k].keys()):
                    if key in self.SKIP_INFO_KEYS:
                        continue
                    text.append(u"\t\t%s: %s" % (key, role_info[k][key]))
            else:
                text.append(u"\t%s: %s" % (k, role_info[k]))

        return u'\n'.join(text)

    #
    # Execute Actions
    #

    def execute_info(self):
        """
        prints out detailed information about an installed role as well as info available from the galaxy API.
        """

        if len(self.args) == 0:
            # the user needs to specify a role
            raise AnsibleOptionsError("- you must specify a user/role name")

        roles_path = self.options.roles_path

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
            if not self.options.offline:
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
        uses the args list of roles to be installed, unless -f was specified. The list of roles
        can be a name (which will be downloaded via the galaxy API and github), or it can be a local .tar.gz file.
        """

        #role_file = self.options.role_file
        role_file = None

        if len(self.args) == 0 and role_file is None:
            # the user needs to specify one of either --role-file or specify a single user/role name
            raise AnsibleOptionsError("- you must specify a user/role name or a roles file")

        #no_deps = self.options.no_deps
        no_deps = False
        force = self.options.force

        roles_left = []
        """
        if role_file:
            try:
                with open(role_file, 'r') as f:
                    if role_file.endswith('.yaml') or role_file.endswith('.yml'):
                        try:
                            required_roles = yaml.safe_load(f.read())
                        except Exception as e:
                            raise AnsibleError("Unable to load data from the requirements file: %s" % role_file)

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
                        display.deprecated("going forward only the yaml format will be supported", version="2.6")
                        # roles listed in a file, one per line
                        for rline in f.readlines():
                            if rline.startswith("#") or rline.strip() == '':
                                continue
                            display.debug('found role %s in text file' % str(rline))
                            role = RoleRequirement.role_yaml_parse(rline.strip())
                            roles_left.append(GalaxyRole(self.galaxy, **role))
            except (IOError, OSError) as e:
                raise AnsibleError('Unable to open %s: %s' % (role_file, str(e)))
        else:
        """
        if True:
            # roles were specified directly, so we'll just go out grab them
            # (and their dependencies, unless the user doesn't want us to).
            for rname in self.args:
                role = RoleRequirement.role_yaml_parse(rname.strip())
                roles_left.append(GalaxyRole(self.galaxy, **role))

        for role in roles_left:
            # only process roles in roles files when names matches if given
            if role_file and self.args and role.name not in self.args:
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
                    display.display('- %s is already installed, skipping.' % str(role))
                    continue

            try:
                installed = role.install()
            except AnsibleError as e:
                display.warning("- %s was NOT installed successfully: %s " % (role.name, str(e)))
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
                                display.display('- adding dependency: %s' % str(dep_role))
                                roles_left.append(dep_role)
                            else:
                                display.display('- dependency %s already pending installation.' % dep_role.name)
                        else:
                            if dep_role.install_info['version'] != dep_role.version:
                                display.warning('- dependency %s from role %s differs from already installed version (%s), skipping' %
                                                (str(dep_role), role.name, dep_role.install_info['version']))
                            else:
                                display.display('- dependency %s is already installed, skipping.' % dep_role.name)

            if not installed:
                display.warning("- %s was NOT installed successfully." % role.name)
                self.exit_without_ignore()

            install_path = self.options.modules_path[0]
            makedirs_safe(install_path)
            for roles in roles_left:
                library_path = os.path.join(roles.path, 'library')
                modules = glob.glob(os.path.join(library_path, '*'))
                if not modules:
                    # uninstall role
                    role = GalaxyRole(self.galaxy, role_name)
                    role.remove()
                    continue

                for module in modules:
                    os.symlink(module, os.path.join(self.options.modules_path[0], os.path.basename(module)))
        return 0

    def execute_remove(self):
        """
        removes the list of roles passed as arguments from the local system.
        """

        if len(self.args) == 0:
            raise AnsibleOptionsError('- you must specify at least one role to remove.')

        install_path = self.options.modules_path[0]
        for role_name in self.args:
            role = GalaxyRole(self.galaxy, role_name)
            role_path = role.path
            modules = glob.glob(os.path.join(role_path, 'library', '*'))
            try:
                if role.remove():
                    display.display('- successfully removed %s' % role_name)
                    installed_modules = os.listdir(install_path)
                    for module in modules:
                        if os.path.basename(module) in installed_modules and os.path.realpath(module) == os.path.realpath(os.path.join(install_path, os.path.basename(module))):
                            os.unlink(os.path.join(install_path, os.path.basename(module)))

                else:
                    display.display('- %s is not installed, skipping.' % role_name)
            except Exception as e:
                raise AnsibleError("Failed to remove role %s: %s" % (role_name, str(e)))

        return 0

    def execute_list(self):
        """
        lists the roles installed on the local system or matches a single role passed as an argument.
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
            roles_path = self.options.roles_path
            for path in roles_path:
                role_path = os.path.expanduser(path)
                if not os.path.exists(role_path):
                    raise AnsibleOptionsError("- the path %s does not exist. Please specify a valid path with --roles-path" % role_path)
                elif not os.path.isdir(role_path):
                    raise AnsibleOptionsError("- %s exists, but it is not a directory. Please specify a valid path with --roles-path" % role_path)
                path_files = os.listdir(role_path)
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
        ''' searches for roles on the Ansible Galaxy server'''

        # Take comma separated string values for backwards compatibility
        if hasattr(self.options, 'galaxy_tags') and self.options.galaxy_tags:
            tags = set()
            for tag_set in self.options.galaxy_tags:
                tags.update(t.strip() for t in tag_set.split(u','))
            self.options.galaxy_tags = list(tags)

        self.options.galaxy_tags.append(self.options.type)

        page_size = 1000
        search = None

        if self.args:
            terms = []
            for i in range(len(self.args)):
                terms.append(self.args.pop())
            search = '+'.join(terms[::-1])

        if not search and not self.options.platforms and not self.options.galaxy_tags and not self.options.author:
            raise AnsibleError("Invalid query. At least one search term, platform, galaxy tag or author must be provided.")

        response = self.api.search_roles(search, platforms=self.options.platforms,
                                         tags=self.options.galaxy_tags, author=self.options.author, page_size=page_size)

        if response['count'] == 0:
            display.display("No %s plugins match your search." % self.options.type, color=C.COLOR_ERROR)
            return True

        data = [u'']

        if response['count'] > page_size:
            data.append(u"Found %d %s plugins matching your search. Showing first %s." % (response['count'], self.options.type, page_size))
        else:
            data.append(u"Found %d %s plugins matching your search:" % (response['count'], self.options.type))

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
