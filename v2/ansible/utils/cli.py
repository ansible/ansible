# (c) 2012-2014, Michael DeHaan <michael.dehaan@gmail.com>
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

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import operator
import optparse
import os
import time
import yaml

from ansible import __version__
from ansible import constants as C

# FIXME: documentation for methods here, which have mostly been
#        copied directly over from the old utils/__init__.py

class SortedOptParser(optparse.OptionParser):
    '''Optparser which sorts the options by opt before outputting --help'''

    def format_help(self, formatter=None):
        self.option_list.sort(key=operator.methodcaller('get_opt_string'))
        return optparse.OptionParser.format_help(self, formatter=None)

def base_parser(usage="", output_opts=False, runas_opts=False,
    async_opts=False, connect_opts=False, subset_opts=False, check_opts=False, diff_opts=False):
    ''' create an options parser for any ansible script '''

    parser = SortedOptParser(usage, version=version("%prog"))

    parser.add_option('-v','--verbose', dest='verbosity', default=0, action="count",
        help="verbose mode (-vvv for more, -vvvv to enable connection debugging)")
    parser.add_option('-f','--forks', dest='forks', default=C.DEFAULT_FORKS, type='int',
        help="specify number of parallel processes to use (default=%s)" % C.DEFAULT_FORKS)
    parser.add_option('-i', '--inventory-file', dest='inventory',
        help="specify inventory host file (default=%s)" % C.DEFAULT_HOST_LIST,
        default=C.DEFAULT_HOST_LIST)
    parser.add_option('-k', '--ask-pass', default=False, dest='ask_pass', action='store_true',
        help='ask for SSH password')
    parser.add_option('--private-key', default=C.DEFAULT_PRIVATE_KEY_FILE, dest='private_key_file',
        help='use this file to authenticate the connection')
    parser.add_option('-K', '--ask-sudo-pass', default=False, dest='ask_sudo_pass', action='store_true',
        help='ask for sudo password')
    parser.add_option('--ask-su-pass', default=False, dest='ask_su_pass', action='store_true',
        help='ask for su password')
    parser.add_option('--ask-vault-pass', default=False, dest='ask_vault_pass', action='store_true',
        help='ask for vault password')
    parser.add_option('--vault-password-file', default=C.DEFAULT_VAULT_PASSWORD_FILE,
        dest='vault_password_file', help="vault password file")
    parser.add_option('--list-hosts', dest='listhosts', action='store_true',
        help='outputs a list of matching hosts; does not execute anything else')
    parser.add_option('-M', '--module-path', dest='module_path',
        help="specify path(s) to module library (default=%s)" % C.DEFAULT_MODULE_PATH,
        default=None)

    if subset_opts:
        parser.add_option('-l', '--limit', default=C.DEFAULT_SUBSET, dest='subset',
            help='further limit selected hosts to an additional pattern')

    parser.add_option('-T', '--timeout', default=C.DEFAULT_TIMEOUT, type='int',
        dest='timeout',
        help="override the SSH timeout in seconds (default=%s)" % C.DEFAULT_TIMEOUT)

    if output_opts:
        parser.add_option('-o', '--one-line', dest='one_line', action='store_true',
            help='condense output')
        parser.add_option('-t', '--tree', dest='tree', default=None,
            help='log output to this directory')

    if runas_opts:
        parser.add_option("-s", "--sudo", default=C.DEFAULT_SUDO, action="store_true",
            dest='sudo', help="run operations with sudo (nopasswd)")
        parser.add_option('-U', '--sudo-user', dest='sudo_user', default=None,
                          help='desired sudo user (default=root)')  # Can't default to root because we need to detect when this option was given
        parser.add_option('-u', '--user', default=C.DEFAULT_REMOTE_USER,
            dest='remote_user', help='connect as this user (default=%s)' % C.DEFAULT_REMOTE_USER)

        parser.add_option('-S', '--su', default=C.DEFAULT_SU,
                          action='store_true', help='run operations with su')
        parser.add_option('-R', '--su-user', help='run operations with su as this '
                                                  'user (default=%s)' % C.DEFAULT_SU_USER)

    if connect_opts:
        parser.add_option('-c', '--connection', dest='connection',
                          default=C.DEFAULT_TRANSPORT,
                          help="connection type to use (default=%s)" % C.DEFAULT_TRANSPORT)

    if async_opts:
        parser.add_option('-P', '--poll', default=C.DEFAULT_POLL_INTERVAL, type='int',
            dest='poll_interval',
            help="set the poll interval if using -B (default=%s)" % C.DEFAULT_POLL_INTERVAL)
        parser.add_option('-B', '--background', dest='seconds', type='int', default=0,
            help='run asynchronously, failing after X seconds (default=N/A)')

    if check_opts:
        parser.add_option("-C", "--check", default=False, dest='check', action='store_true',
            help="don't make any changes; instead, try to predict some of the changes that may occur"
        )

    if diff_opts:
        parser.add_option("-D", "--diff", default=False, dest='diff', action='store_true',
            help="when changing (small) files and templates, show the differences in those files; works great with --check"
        )


    return parser

def version(prog):
    result = "{0} {1}".format(prog, __version__)
    gitinfo = _gitinfo()
    if gitinfo:
        result = result + " {0}".format(gitinfo)
    result = result + "\n  configured module search path = %s" % C.DEFAULT_MODULE_PATH
    return result

def version_info(gitinfo=False):
    if gitinfo:
        # expensive call, user with care
        ansible_version_string = version('')
    else:
        ansible_version_string = __version__
    ansible_version = ansible_version_string.split()[0]
    ansible_versions = ansible_version.split('.')
    for counter in range(len(ansible_versions)):
        if ansible_versions[counter] == "":
            ansible_versions[counter] = 0
        try:
            ansible_versions[counter] = int(ansible_versions[counter])
        except:
            pass
    if len(ansible_versions) < 3:
        for counter in range(len(ansible_versions), 3):
            ansible_versions.append(0)
    return {'string':      ansible_version_string.strip(),
            'full':        ansible_version,
            'major':       ansible_versions[0],
            'minor':       ansible_versions[1],
            'revision':    ansible_versions[2]}

def _git_repo_info(repo_path):
    ''' returns a string containing git branch, commit id and commit date '''
    result = None
    if os.path.exists(repo_path):
        # Check if the .git is a file. If it is a file, it means that we are in a submodule structure.
        if os.path.isfile(repo_path):
            try:
                gitdir = yaml.safe_load(open(repo_path)).get('gitdir')
                # There is a possibility the .git file to have an absolute path.
                if os.path.isabs(gitdir):
                    repo_path = gitdir
                else:
                    repo_path = os.path.join(repo_path[:-4], gitdir)
            except (IOError, AttributeError):
                return ''
        f = open(os.path.join(repo_path, "HEAD"))
        branch = f.readline().split('/')[-1].rstrip("\n")
        f.close()
        branch_path = os.path.join(repo_path, "refs", "heads", branch)
        if os.path.exists(branch_path):
            f = open(branch_path)
            commit = f.readline()[:10]
            f.close()
        else:
            # detached HEAD
            commit = branch[:10]
            branch = 'detached HEAD'
            branch_path = os.path.join(repo_path, "HEAD")

        date = time.localtime(os.stat(branch_path).st_mtime)
        if time.daylight == 0:
            offset = time.timezone
        else:
            offset = time.altzone
        result = "({0} {1}) last updated {2} (GMT {3:+04d})".format(branch, commit,
            time.strftime("%Y/%m/%d %H:%M:%S", date), int(offset / -36))
    else:
        result = ''
    return result

def _gitinfo():
    basedir = os.path.join(os.path.dirname(__file__), '..', '..', '..')
    repo_path = os.path.join(basedir, '.git')
    result = _git_repo_info(repo_path)
    submodules = os.path.join(basedir, '.gitmodules')
    if not os.path.exists(submodules):
       return result
    f = open(submodules)
    for line in f:
        tokens = line.strip().split(' ')
        if tokens[0] == 'path':
            submodule_path = tokens[2]
            submodule_info =_git_repo_info(os.path.join(basedir, submodule_path, '.git'))
            if not submodule_info:
                submodule_info = ' not found - use git submodule update --init ' + submodule_path
            result += "\n  {0}: {1}".format(submodule_path, submodule_info)
    f.close()
    return result

