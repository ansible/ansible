# Copyright: (c) 2018, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import operator
import optparse
import os
import os.path
import sys
import time
import yaml

import ansible
from ansible import constants as C
from ansible.module_utils.six import string_types
from ansible.module_utils._text import to_native
from ansible.release import __version__
from ansible.utils.path import unfrackpath


#
# Special purpose OptionParsers
#

class SortedOptParser(optparse.OptionParser):
    """Optparser which sorts the options by opt before outputting --help"""

    def format_help(self, formatter=None, epilog=None):
        self.option_list.sort(key=operator.methodcaller('get_opt_string'))
        return optparse.OptionParser.format_help(self, formatter=None)


# Note: Inherit from SortedOptParser so that we get our format_help method
class InvalidOptsParser(SortedOptParser):
    """Ignore invalid options.

    Meant for the special case where we need to take care of help and version but may not know the
    full range of options yet.

    .. seealso::
        See it in use in ansible.cli.CLI.set_action
    """
    def __init__(self, parser):
        # Since this is special purposed to just handle help and version, we
        # take a pre-existing option parser here and set our options from
        # that.  This allows us to give accurate help based on the given
        # option parser.
        SortedOptParser.__init__(self, usage=parser.usage,
                                 option_list=parser.option_list,
                                 option_class=parser.option_class,
                                 conflict_handler=parser.conflict_handler,
                                 description=parser.description,
                                 formatter=parser.formatter,
                                 add_help_option=False,
                                 prog=parser.prog,
                                 epilog=parser.epilog)
        self.version = parser.version

    def _process_long_opt(self, rargs, values):
        try:
            optparse.OptionParser._process_long_opt(self, rargs, values)
        except optparse.BadOptionError:
            pass

    def _process_short_opts(self, rargs, values):
        try:
            optparse.OptionParser._process_short_opts(self, rargs, values)
        except optparse.BadOptionError:
            pass


#
# Callbacks to validate and normalize Options
#

def unfrack_paths(option, opt, value, parser):
    """Turn an Option's value into a list of paths in Ansible locations"""
    paths = getattr(parser.values, option.dest)
    if paths is None:
        paths = []

    if isinstance(value, string_types):
        paths[:0] = [unfrackpath(x) for x in value.split(os.pathsep) if x]
    elif isinstance(value, list):
        paths[:0] = [unfrackpath(x) for x in value if x]
    else:
        pass  # FIXME: should we raise options error?

    setattr(parser.values, option.dest, paths)


def unfrack_path(option, opt, value, parser):
    """Turn an Option's data into a single path in Ansible locations"""
    if value != '-':
        setattr(parser.values, option.dest, unfrackpath(value))
    else:
        setattr(parser.values, option.dest, value)


def _git_repo_info(repo_path):
    """ returns a string containing git branch, commit id and commit date """
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
        with open(os.path.join(repo_path, "HEAD")) as f:
            line = f.readline().rstrip("\n")
            if line.startswith("ref:"):
                branch_path = os.path.join(repo_path, line[5:])
            else:
                branch_path = None
        if branch_path and os.path.exists(branch_path):
            branch = '/'.join(line.split('/')[2:])
            with open(branch_path) as f:
                commit = f.readline()[:10]
        else:
            # detached HEAD
            commit = line[:10]
            branch = 'detached HEAD'
            branch_path = os.path.join(repo_path, "HEAD")

        date = time.localtime(os.stat(branch_path).st_mtime)
        if time.daylight == 0:
            offset = time.timezone
        else:
            offset = time.altzone
        result = "({0} {1}) last updated {2} (GMT {3:+04d})".format(branch, commit, time.strftime("%Y/%m/%d %H:%M:%S", date), int(offset / -36))
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

    with open(submodules) as f:
        for line in f:
            tokens = line.strip().split(' ')
            if tokens[0] == 'path':
                submodule_path = tokens[2]
                submodule_info = _git_repo_info(os.path.join(basedir, submodule_path, '.git'))
                if not submodule_info:
                    submodule_info = ' not found - use git submodule update --init ' + submodule_path
                result += "\n  {0}: {1}".format(submodule_path, submodule_info)
    return result


def version(prog=None):
    """ return ansible version """
    if prog:
        result = " ".join((prog, __version__))
    else:
        result = __version__

    gitinfo = _gitinfo()
    if gitinfo:
        result = result + " {0}".format(gitinfo)
    result += "\n  config file = %s" % C.CONFIG_FILE
    if C.DEFAULT_MODULE_PATH is None:
        cpath = "Default w/o overrides"
    else:
        cpath = C.DEFAULT_MODULE_PATH
    result = result + "\n  configured module search path = %s" % cpath
    result = result + "\n  ansible python module location = %s" % ':'.join(ansible.__path__)
    result = result + "\n  executable location = %s" % sys.argv[0]
    result = result + "\n  python version = %s" % ''.join(sys.version.splitlines())
    return result


#
# Functions to add pre-canned options to an OptionParser
#

def create_base_parser(usage="", desc=None, epilog=None):
    """
    Create an options parser for all ansible scripts
    """
    # base opts
    parser = SortedOptParser(usage, version=to_native(version("%prog")), description=desc, epilog=epilog)
    parser.remove_option('--version')
    version_help = "show program's version number, config file location, configured module search path," \
                   " module location, executable location and exit"
    parser.add_option('--version', action="version", help=version_help)
    parser.add_option('-v', '--verbose', dest='verbosity', default=C.DEFAULT_VERBOSITY, action="count",
                      help="verbose mode (-vvv for more, -vvvv to enable connection debugging)")
    return parser


def add_async_options(parser):
    """Add options for commands which can launch async tasks"""
    parser.add_option('-P', '--poll', default=C.DEFAULT_POLL_INTERVAL, type='int', dest='poll_interval',
                      help="set the poll interval if using -B (default=%s)" % C.DEFAULT_POLL_INTERVAL)
    parser.add_option('-B', '--background', dest='seconds', type='int', default=0,
                      help='run asynchronously, failing after X seconds (default=N/A)')


def add_basedir_options(parser):
    """Add options for commands which can set a playbook basedir"""
    parser.add_option('--playbook-dir', default=None, dest='basedir', action='store',
                      help="Since this tool does not use playbooks, use this as a substitute playbook directory."
                           "This sets the relative path for many features including roles/ group_vars/ etc.")


def add_check_options(parser):
    """Add options for commands which can run with diagnostic information of tasks"""
    parser.add_option("-C", "--check", default=False, dest='check', action='store_true',
                      help="don't make any changes; instead, try to predict some of the changes that may occur")
    parser.add_option('--syntax-check', dest='syntax', action='store_true',
                      help="perform a syntax check on the playbook, but do not execute it")
    parser.add_option("-D", "--diff", default=C.DIFF_ALWAYS, dest='diff', action='store_true',
                      help="when changing (small) files and templates, show the differences in those"
                      " files; works great with --check")


def add_connect_options(parser):
    """Add options for commands which need to connection to other hosts"""
    connect_group = optparse.OptionGroup(parser, "Connection Options", "control as whom and how to connect to hosts")

    connect_group.add_option('-k', '--ask-pass', default=C.DEFAULT_ASK_PASS, dest='ask_pass', action='store_true',
                             help='ask for connection password')
    connect_group.add_option('--private-key', '--key-file', default=C.DEFAULT_PRIVATE_KEY_FILE, dest='private_key_file',
                             help='use this file to authenticate the connection', action="callback", callback=unfrack_path, type='string')
    connect_group.add_option('-u', '--user', default=C.DEFAULT_REMOTE_USER, dest='remote_user',
                             help='connect as this user (default=%s)' % C.DEFAULT_REMOTE_USER)
    connect_group.add_option('-c', '--connection', dest='connection', default=C.DEFAULT_TRANSPORT,
                             help="connection type to use (default=%s)" % C.DEFAULT_TRANSPORT)
    connect_group.add_option('-T', '--timeout', default=C.DEFAULT_TIMEOUT, type='int', dest='timeout',
                             help="override the connection timeout in seconds (default=%s)" % C.DEFAULT_TIMEOUT)
    connect_group.add_option('--ssh-common-args', default='', dest='ssh_common_args',
                             help="specify common arguments to pass to sftp/scp/ssh (e.g. ProxyCommand)")
    connect_group.add_option('--sftp-extra-args', default='', dest='sftp_extra_args',
                             help="specify extra arguments to pass to sftp only (e.g. -f, -l)")
    connect_group.add_option('--scp-extra-args', default='', dest='scp_extra_args',
                             help="specify extra arguments to pass to scp only (e.g. -l)")
    connect_group.add_option('--ssh-extra-args', default='', dest='ssh_extra_args',
                             help="specify extra arguments to pass to ssh only (e.g. -R)")

    parser.add_option_group(connect_group)


def add_fork_options(parser):
    """Add options for commands that can fork worker processes"""
    parser.add_option('-f', '--forks', dest='forks', default=C.DEFAULT_FORKS, type='int',
                      help="specify number of parallel processes to use (default=%s)" % C.DEFAULT_FORKS)


def add_inventory_options(parser):
    """Add options for commands that utilize inventory"""
    parser.add_option('-i', '--inventory', '--inventory-file', dest='inventory', action="append",
                      help="specify inventory host path or comma separated host list. --inventory-file is deprecated")
    parser.add_option('--list-hosts', dest='listhosts', action='store_true',
                      help='outputs a list of matching hosts; does not execute anything else')
    parser.add_option('-l', '--limit', default=C.DEFAULT_SUBSET, dest='subset',
                      help='further limit selected hosts to an additional pattern')


def add_meta_options(parser):
    """Add options for commands which can launch meta tasks from the command line"""
    parser.add_option('--force-handlers', default=C.DEFAULT_FORCE_HANDLERS, dest='force_handlers', action='store_true',
                      help="run handlers even if a task fails")
    parser.add_option('--flush-cache', dest='flush_cache', action='store_true',
                      help="clear the fact cache for every host in inventory")


def add_module_options(parser):
    """Add options for commands that load modules"""

    module_path = C.config.get_configuration_definition('DEFAULT_MODULE_PATH').get('default', '')
    parser.add_option('-M', '--module-path', dest='module_path', default=None,
                      help="prepend colon-separated path(s) to module library (default=%s)" % module_path,
                      action="callback", callback=unfrack_paths, type='str')


def add_output_options(parser):
    """Add options for commands which can change their output"""
    parser.add_option('-o', '--one-line', dest='one_line', action='store_true',
                      help='condense output')
    parser.add_option('-t', '--tree', dest='tree', default=None,
                      help='log output to this directory')


def add_runas_options(parser):
    """
    Add options for commands which can run tasks as another user

    Note that this includes the options from add_runas_prompt_options().  Only one of these
    functions should be used.
    """
    runas_group = optparse.OptionGroup(parser, "Privilege Escalation Options", "control how and which user you become as on target hosts")

    # consolidated privilege escalation (become)
    runas_group.add_option("-b", "--become", default=C.DEFAULT_BECOME, action="store_true", dest='become',
                           help="run operations with become (does not imply password prompting)")
    runas_group.add_option('--become-method', dest='become_method', default=C.DEFAULT_BECOME_METHOD,
                           help="privilege escalation method to use (default=%default), use "
                                "`ansible-doc -t become -l` to list valid choices.")
    runas_group.add_option('--become-user', default=None, dest='become_user', type='string',
                           help='run operations as this user (default=%s)' % C.DEFAULT_BECOME_USER)

    add_runas_prompt_options(parser, runas_group=runas_group)


def add_runas_prompt_options(parser, runas_group=None):
    """
    Add options for commands which need to prompt for privilege escalation credentials

    Note that add_runas_options() includes these options already.  Only one of the two functions
    should be used.
    """
    if runas_group is None:
        runas_group = optparse.OptionGroup(parser, "Privilege Escalation Options",
                                           "control how and which user you become as on target hosts")

    runas_group.add_option('-K', '--ask-become-pass', dest='become_ask_pass', action='store_true',
                           help='ask for privilege escalation password', default=C.DEFAULT_BECOME_ASK_PASS)

    parser.add_option_group(runas_group)


def add_runtask_options(parser):
    """Add options for commands that run a task"""
    parser.add_option('-e', '--extra-vars', dest="extra_vars", action="append",
                      help="set additional variables as key=value or YAML/JSON, if filename prepend with @", default=[])


def add_subset_options(parser):
    """Add options for commands which can run a subset of tasks"""
    parser.add_option('-t', '--tags', dest='tags', default=C.TAGS_RUN, action='append',
                      help="only run plays and tasks tagged with these values")
    parser.add_option('--skip-tags', dest='skip_tags', default=C.TAGS_SKIP, action='append',
                      help="only run plays and tasks whose tags do not match these values")


def add_vault_options(parser):
    """Add options for loading vault files"""
    parser.add_option('--ask-vault-pass', default=C.DEFAULT_ASK_VAULT_PASS, dest='ask_vault_pass', action='store_true',
                      help='ask for vault password')
    parser.add_option('--vault-password-file', default=[], dest='vault_password_files',
                      help="vault password file", action="callback", callback=unfrack_paths, type='string')
    parser.add_option('--vault-id', default=[], dest='vault_ids', action='append', type='string',
                      help='the vault identity to use')


def add_vault_rekey_options(parser):
    """Add options for commands which can edit/rekey a vault file"""
    parser.add_option('--new-vault-password-file', default=None, dest='new_vault_password_file',
                      help="new vault password file for rekey", action="callback", callback=unfrack_path, type='string')
    parser.add_option('--new-vault-id', default=None, dest='new_vault_id', type='string',
                      help='the new vault identity to use for rekey')
