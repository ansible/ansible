# (c) 2012-2014, Michael DeHaan <michael.dehaan@gmail.com>
# (c) 2016, Toshio Kuratomi <tkuratomi@ansible.com>
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

import getpass
import operator
import optparse
import os
import subprocess
import re
import sys
import time
import yaml

from abc import ABCMeta, abstractmethod

import ansible
from ansible import constants as C
from ansible.errors import AnsibleOptionsError, AnsibleError
from ansible.inventory.manager import InventoryManager
from ansible.module_utils.six import with_metaclass, string_types
from ansible.module_utils._text import to_bytes, to_text
from ansible.parsing.dataloader import DataLoader
from ansible.release import __version__
from ansible.utils.path import unfrackpath
from ansible.utils.vars import load_extra_vars, load_options_vars
from ansible.vars.manager import VariableManager
from ansible.parsing.vault import PromptVaultSecret, get_file_vault_secret

try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display
    display = Display()


class SortedOptParser(optparse.OptionParser):
    '''Optparser which sorts the options by opt before outputting --help'''

    def format_help(self, formatter=None, epilog=None):
        self.option_list.sort(key=operator.methodcaller('get_opt_string'))
        return optparse.OptionParser.format_help(self, formatter=None)


# Note: Inherit from SortedOptParser so that we get our format_help method
class InvalidOptsParser(SortedOptParser):
    '''Ignore invalid options.

    Meant for the special case where we need to take care of help and version
    but may not know the full range of options yet.  (See it in use in set_action)
    '''
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


class CLI(with_metaclass(ABCMeta, object)):
    ''' code behind bin/ansible* programs '''

    VALID_ACTIONS = []

    _ITALIC = re.compile(r"I\(([^)]+)\)")
    _BOLD = re.compile(r"B\(([^)]+)\)")
    _MODULE = re.compile(r"M\(([^)]+)\)")
    _URL = re.compile(r"U\(([^)]+)\)")
    _CONST = re.compile(r"C\(([^)]+)\)")

    PAGER = 'less'

    # -F (quit-if-one-screen) -R (allow raw ansi control chars)
    # -S (chop long lines) -X (disable termcap init and de-init)
    LESS_OPTS = 'FRSX'
    SKIP_INVENTORY_DEFAULTS = False

    def __init__(self, args, callback=None):
        """
        Base init method for all command line programs
        """

        self.args = args
        self.options = None
        self.parser = None
        self.action = None
        self.callback = callback

    def set_action(self):
        """
        Get the action the user wants to execute from the sys argv list.
        """
        for i in range(0, len(self.args)):
            arg = self.args[i]
            if arg in self.VALID_ACTIONS:
                self.action = arg
                del self.args[i]
                break

        if not self.action:
            # if we're asked for help or version, we don't need an action.
            # have to use a special purpose Option Parser to figure that out as
            # the standard OptionParser throws an error for unknown options and
            # without knowing action, we only know of a subset of the options
            # that could be legal for this command
            tmp_parser = InvalidOptsParser(self.parser)
            tmp_options, tmp_args = tmp_parser.parse_args(self.args)
            if not(hasattr(tmp_options, 'help') and tmp_options.help) or (hasattr(tmp_options, 'version') and tmp_options.version):
                raise AnsibleOptionsError("Missing required action")

    def execute(self):
        """
        Actually runs a child defined method using the execute_<action> pattern
        """
        fn = getattr(self, "execute_%s" % self.action)
        fn()

    @abstractmethod
    def run(self):
        """Run the ansible command

        Subclasses must implement this method.  It does the actual work of
        running an Ansible command.
        """

        display.vv(to_text(self.parser.get_version()))

        if C.CONFIG_FILE:
            display.v(u"Using %s as config file" % to_text(C.CONFIG_FILE))
        else:
            display.v(u"No config file found; using defaults")

        # warn about deprecated config options
        for deprecated in C.config.DEPRECATED:
            name = deprecated[0]
            why = deprecated[1]['why']
            if 'alternatives' in deprecated[1]:
                alt = ', use %s instead' % deprecated[1]['alternatives']
            else:
                alt = ''
            ver = deprecated[1]['version']
            display.deprecated("%s option, %s %s" % (name, why, alt), version=ver)

        # Errors with configuration entries
        if C.config.UNABLE:
            for unable in C.config.UNABLE:
                display.error("Unable to set correct type for configuration entry for %s: %s" % (unable, C.config.UNABLE[unable]))
            raise AnsibleError("Invalid configuration settings")

    @staticmethod
    def split_vault_id(vault_id):
        # return (before_@, after_@)
        # if no @, return whole string as after_
        if '@' not in vault_id:
            return (None, vault_id)

        parts = vault_id.split('@', 1)
        ret = tuple(parts)
        return ret

    @staticmethod
    def build_vault_ids(vault_ids, vault_password_files=None,
                        ask_vault_pass=None, create_new_password=None,
                        auto_prompt=True):
        vault_password_files = vault_password_files or []
        vault_ids = vault_ids or []

        # convert vault_password_files into vault_ids slugs
        for password_file in vault_password_files:
            id_slug = u'%s@%s' % (C.DEFAULT_VAULT_IDENTITY, password_file)

            # note this makes --vault-id higher precendence than --vault-password-file
            # if we want to intertwingle them in order probably need a cli callback to populate vault_ids
            # used by --vault-id and --vault-password-file
            vault_ids.append(id_slug)

        # if an action needs an encrypt password (create_new_password=True) and we dont
        # have other secrets setup, then automatically add a password prompt as well.
        # prompts cant/shouldnt work without a tty, so dont add prompt secrets
        if ask_vault_pass or (not vault_ids and auto_prompt):

            id_slug = u'%s@%s' % (C.DEFAULT_VAULT_IDENTITY, u'prompt_ask_vault_pass')
            vault_ids.append(id_slug)

        return vault_ids

    # TODO: remove the now unused args
    @staticmethod
    def setup_vault_secrets(loader, vault_ids, vault_password_files=None,
                            ask_vault_pass=None, create_new_password=False,
                            auto_prompt=True):
        # list of tuples
        vault_secrets = []

        # Depending on the vault_id value (including how --ask-vault-pass / --vault-password-file create a vault_id)
        # we need to show different prompts. This is for compat with older Towers that expect a
        # certain vault password prompt format, so 'promp_ask_vault_pass' vault_id gets the old format.
        prompt_formats = {}

        # If there are configured default vault identities, they are considered 'first'
        # so we prepend them to vault_ids (from cli) here

        vault_password_files = vault_password_files or []
        if C.DEFAULT_VAULT_PASSWORD_FILE:
            vault_password_files.append(C.DEFAULT_VAULT_PASSWORD_FILE)

        if create_new_password:
            prompt_formats['prompt'] = ['New vault password (%(vault_id)s): ',
                                        'Confirm vew vault password (%(vault_id)s): ']
            # 2.3 format prompts for --ask-vault-pass
            prompt_formats['prompt_ask_vault_pass'] = ['New Vault password: ',
                                                       'Confirm New Vault password: ']
        else:
            prompt_formats['prompt'] = ['Vault password (%(vault_id)s): ']
            # The format when we use just --ask-vault-pass needs to match 'Vault password:\s*?$'
            prompt_formats['prompt_ask_vault_pass'] = ['Vault password: ']

        vault_ids = CLI.build_vault_ids(vault_ids,
                                        vault_password_files,
                                        ask_vault_pass,
                                        create_new_password,
                                        auto_prompt=auto_prompt)

        for vault_id_slug in vault_ids:
            vault_id_name, vault_id_value = CLI.split_vault_id(vault_id_slug)
            if vault_id_value in ['prompt', 'prompt_ask_vault_pass']:

                # --vault-id some_name@prompt_ask_vault_pass --vault-id other_name@prompt_ask_vault_pass will be a little
                # confusing since it will use the old format without the vault id in the prompt
                built_vault_id = vault_id_name or C.DEFAULT_VAULT_IDENTITY

                # choose the prompt based on --vault-id=prompt or --ask-vault-pass. --ask-vault-pass
                # always gets the old format for Tower compatibility.
                # ie, we used --ask-vault-pass, so we need to use the old vault password prompt
                # format since Tower needs to match on that format.
                prompted_vault_secret = PromptVaultSecret(prompt_formats=prompt_formats[vault_id_value],
                                                          vault_id=built_vault_id)

                # a empty or invalid password from the prompt will warn and continue to the next
                # without erroring globablly
                try:
                    prompted_vault_secret.load()
                except AnsibleError as exc:
                    display.warning('Error in vault password prompt (%s): %s' % (vault_id_name, exc))
                    raise

                vault_secrets.append((built_vault_id, prompted_vault_secret))

                # update loader with new secrets incrementally, so we can load a vault password
                # that is encrypted with a vault secret provided earlier
                loader.set_vault_secrets(vault_secrets)
                continue

            # assuming anything else is a password file
            display.vvvvv('Reading vault password file: %s' % vault_id_value)
            # read vault_pass from a file
            file_vault_secret = get_file_vault_secret(filename=vault_id_value,
                                                      vault_id=vault_id_name,
                                                      loader=loader)

            # an invalid password file will error globally
            try:
                file_vault_secret.load()
            except AnsibleError as exc:
                display.warning('Error in vault password file loading (%s): %s' % (vault_id_name, exc))
                raise

            if vault_id_name:
                vault_secrets.append((vault_id_name, file_vault_secret))
            else:
                vault_secrets.append((C.DEFAULT_VAULT_IDENTITY, file_vault_secret))

            # update loader with as-yet-known vault secrets
            loader.set_vault_secrets(vault_secrets)

        return vault_secrets

    def ask_passwords(self):
        ''' prompt for connection and become passwords if needed '''

        op = self.options
        sshpass = None
        becomepass = None
        become_prompt = ''

        become_prompt_method = "BECOME" if C.AGNOSTIC_BECOME_PROMPT else op.become_method.upper()

        try:
            if op.ask_pass:
                sshpass = getpass.getpass(prompt="SSH password: ")
                become_prompt = "%s password[defaults to SSH password]: " % become_prompt_method
                if sshpass:
                    sshpass = to_bytes(sshpass, errors='strict', nonstring='simplerepr')
            else:
                become_prompt = "%s password: " % become_prompt_method

            if op.become_ask_pass:
                becomepass = getpass.getpass(prompt=become_prompt)
                if op.ask_pass and becomepass == '':
                    becomepass = sshpass
                if becomepass:
                    becomepass = to_bytes(becomepass)
        except EOFError:
            pass

        return (sshpass, becomepass)

    def normalize_become_options(self):
        ''' this keeps backwards compatibility with sudo/su self.options '''
        self.options.become_ask_pass = self.options.become_ask_pass or self.options.ask_sudo_pass or self.options.ask_su_pass or C.DEFAULT_BECOME_ASK_PASS
        self.options.become_user = self.options.become_user or self.options.sudo_user or self.options.su_user or C.DEFAULT_BECOME_USER

        def _dep(which):
            display.deprecated('The %s command line option has been deprecated in favor of the "become" command line arguments' % which, '2.6')

        if self.options.become:
            pass
        elif self.options.sudo:
            self.options.become = True
            self.options.become_method = 'sudo'
            _dep('sudo')
        elif self.options.su:
            self.options.become = True
            self.options.become_method = 'su'
            _dep('su')

        # other deprecations:
        if self.options.ask_sudo_pass or self.options.sudo_user:
            _dep('sudo')
        if self.options.ask_su_pass or self.options.su_user:
            _dep('su')

    def validate_conflicts(self, vault_opts=False, runas_opts=False, fork_opts=False, vault_rekey_opts=False):
        ''' check for conflicting options '''

        op = self.options

        if vault_opts:
            # Check for vault related conflicts
            if (op.ask_vault_pass and op.vault_password_files):
                self.parser.error("--ask-vault-pass and --vault-password-file are mutually exclusive")

        if vault_rekey_opts:
            if (op.new_vault_id and op.new_vault_password_file):
                self.parser.error("--new-vault-password-file and --new-vault-id are mutually exclusive")

        if runas_opts:
            # Check for privilege escalation conflicts
            if ((op.su or op.su_user) and (op.sudo or op.sudo_user) or
                    (op.su or op.su_user) and (op.become or op.become_user) or
                    (op.sudo or op.sudo_user) and (op.become or op.become_user)):

                self.parser.error("Sudo arguments ('--sudo', '--sudo-user', and '--ask-sudo-pass') and su arguments ('--su', '--su-user', and '--ask-su-pass') "
                                  "and become arguments ('--become', '--become-user', and '--ask-become-pass') are exclusive of each other")

        if fork_opts:
            if op.forks < 1:
                self.parser.error("The number of processes (--forks) must be >= 1")

    @staticmethod
    def unfrack_paths(option, opt, value, parser):
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

    @staticmethod
    def unfrack_path(option, opt, value, parser):
        if value != '-':
            setattr(parser.values, option.dest, unfrackpath(value))
        else:
            setattr(parser.values, option.dest, value)

    @staticmethod
    def base_parser(usage="", output_opts=False, runas_opts=False, meta_opts=False, runtask_opts=False, vault_opts=False, module_opts=False,
                    async_opts=False, connect_opts=False, subset_opts=False, check_opts=False, inventory_opts=False, epilog=None, fork_opts=False,
                    runas_prompt_opts=False, desc=None, basedir_opts=False, vault_rekey_opts=False):
        ''' create an options parser for most ansible scripts '''

        # base opts
        parser = SortedOptParser(usage, version=CLI.version("%prog"), description=desc, epilog=epilog)
        parser.add_option('-v', '--verbose', dest='verbosity', default=C.DEFAULT_VERBOSITY, action="count",
                          help="verbose mode (-vvv for more, -vvvv to enable connection debugging)")

        if inventory_opts:
            parser.add_option('-i', '--inventory', '--inventory-file', dest='inventory', action="append",
                              help="specify inventory host path or comma separated host list. --inventory-file is deprecated")
            parser.add_option('--list-hosts', dest='listhosts', action='store_true',
                              help='outputs a list of matching hosts; does not execute anything else')
            parser.add_option('-l', '--limit', default=C.DEFAULT_SUBSET, dest='subset',
                              help='further limit selected hosts to an additional pattern')

        if module_opts:
            parser.add_option('-M', '--module-path', dest='module_path', default=None,
                              help="prepend colon-separated path(s) to module library (default=%s)" % C.DEFAULT_MODULE_PATH,
                              action="callback", callback=CLI.unfrack_paths, type='str')
        if runtask_opts:
            parser.add_option('-e', '--extra-vars', dest="extra_vars", action="append",
                              help="set additional variables as key=value or YAML/JSON, if filename prepend with @", default=[])

        if fork_opts:
            parser.add_option('-f', '--forks', dest='forks', default=C.DEFAULT_FORKS, type='int',
                              help="specify number of parallel processes to use (default=%s)" % C.DEFAULT_FORKS)

        if vault_opts:
            parser.add_option('--ask-vault-pass', default=C.DEFAULT_ASK_VAULT_PASS, dest='ask_vault_pass', action='store_true',
                              help='ask for vault password')
            parser.add_option('--vault-password-file', default=[], dest='vault_password_files',
                              help="vault password file", action="callback", callback=CLI.unfrack_paths, type='string')
            parser.add_option('--vault-id', default=[], dest='vault_ids', action='append', type='string',
                              help='the vault identity to use')

        if vault_rekey_opts:
            parser.add_option('--new-vault-password-file', default=None, dest='new_vault_password_file',
                              help="new vault password file for rekey", action="callback", callback=CLI.unfrack_path, type='string')
            parser.add_option('--new-vault-id', default=None, dest='new_vault_id', type='string',
                              help='the new vault identity to use for rekey')

        if subset_opts:
            parser.add_option('-t', '--tags', dest='tags', default=C.TAGS_RUN, action='append',
                              help="only run plays and tasks tagged with these values")
            parser.add_option('--skip-tags', dest='skip_tags', default=C.TAGS_SKIP, action='append',
                              help="only run plays and tasks whose tags do not match these values")

        if output_opts:
            parser.add_option('-o', '--one-line', dest='one_line', action='store_true',
                              help='condense output')
            parser.add_option('-t', '--tree', dest='tree', default=None,
                              help='log output to this directory')

        if connect_opts:
            connect_group = optparse.OptionGroup(parser, "Connection Options", "control as whom and how to connect to hosts")
            connect_group.add_option('-k', '--ask-pass', default=C.DEFAULT_ASK_PASS, dest='ask_pass', action='store_true',
                                     help='ask for connection password')
            connect_group.add_option('--private-key', '--key-file', default=C.DEFAULT_PRIVATE_KEY_FILE, dest='private_key_file',
                                     help='use this file to authenticate the connection', action="callback", callback=CLI.unfrack_path, type='string')
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

        runas_group = None
        rg = optparse.OptionGroup(parser, "Privilege Escalation Options", "control how and which user you become as on target hosts")
        if runas_opts:
            runas_group = rg
            # priv user defaults to root later on to enable detecting when this option was given here
            runas_group.add_option("-s", "--sudo", default=C.DEFAULT_SUDO, action="store_true", dest='sudo',
                                   help="run operations with sudo (nopasswd) (deprecated, use become)")
            runas_group.add_option('-U', '--sudo-user', dest='sudo_user', default=None,
                                   help='desired sudo user (default=root) (deprecated, use become)')
            runas_group.add_option('-S', '--su', default=C.DEFAULT_SU, action='store_true',
                                   help='run operations with su (deprecated, use become)')
            runas_group.add_option('-R', '--su-user', default=None,
                                   help='run operations with su as this user (default=%s) (deprecated, use become)' % C.DEFAULT_SU_USER)

            # consolidated privilege escalation (become)
            runas_group.add_option("-b", "--become", default=C.DEFAULT_BECOME, action="store_true", dest='become',
                                   help="run operations with become (does not imply password prompting)")
            runas_group.add_option('--become-method', dest='become_method', default=C.DEFAULT_BECOME_METHOD, type='choice', choices=C.BECOME_METHODS,
                                   help="privilege escalation method to use (default=%s), valid choices: [ %s ]" %
                                   (C.DEFAULT_BECOME_METHOD, ' | '.join(C.BECOME_METHODS)))
            runas_group.add_option('--become-user', default=None, dest='become_user', type='string',
                                   help='run operations as this user (default=%s)' % C.DEFAULT_BECOME_USER)

        if runas_opts or runas_prompt_opts:
            if not runas_group:
                runas_group = rg
            runas_group.add_option('--ask-sudo-pass', default=C.DEFAULT_ASK_SUDO_PASS, dest='ask_sudo_pass', action='store_true',
                                   help='ask for sudo password (deprecated, use become)')
            runas_group.add_option('--ask-su-pass', default=C.DEFAULT_ASK_SU_PASS, dest='ask_su_pass', action='store_true',
                                   help='ask for su password (deprecated, use become)')
            runas_group.add_option('-K', '--ask-become-pass', default=False, dest='become_ask_pass', action='store_true',
                                   help='ask for privilege escalation password')

        if runas_group:
            parser.add_option_group(runas_group)

        if async_opts:
            parser.add_option('-P', '--poll', default=C.DEFAULT_POLL_INTERVAL, type='int', dest='poll_interval',
                              help="set the poll interval if using -B (default=%s)" % C.DEFAULT_POLL_INTERVAL)
            parser.add_option('-B', '--background', dest='seconds', type='int', default=0,
                              help='run asynchronously, failing after X seconds (default=N/A)')

        if check_opts:
            parser.add_option("-C", "--check", default=False, dest='check', action='store_true',
                              help="don't make any changes; instead, try to predict some of the changes that may occur")
            parser.add_option('--syntax-check', dest='syntax', action='store_true',
                              help="perform a syntax check on the playbook, but do not execute it")
            parser.add_option("-D", "--diff", default=C.DIFF_ALWAYS, dest='diff', action='store_true',
                              help="when changing (small) files and templates, show the differences in those files; works great with --check")

        if meta_opts:
            parser.add_option('--force-handlers', default=C.DEFAULT_FORCE_HANDLERS, dest='force_handlers', action='store_true',
                              help="run handlers even if a task fails")
            parser.add_option('--flush-cache', dest='flush_cache', action='store_true',
                              help="clear the fact cache for every host in inventory")

        if basedir_opts:
            parser.add_option('--playbook-dir', default=None, dest='basedir', action='store',
                              help="Since this tool does not use playbooks, use this as a subsitute playbook directory."
                                   "This sets the relative path for many features including roles/ group_vars/ etc.")
        return parser

    @abstractmethod
    def parse(self):
        """Parse the command line args

        This method parses the command line arguments.  It uses the parser
        stored in the self.parser attribute and saves the args and options in
        self.args and self.options respectively.

        Subclasses need to implement this method.  They will usually create
        a base_parser, add their own options to the base_parser, and then call
        this method to do the actual parsing.  An implementation will look
        something like this::

            def parse(self):
                parser = super(MyCLI, self).base_parser(usage="My Ansible CLI", inventory_opts=True)
                parser.add_option('--my-option', dest='my_option', action='store')
                self.parser = parser
                super(MyCLI, self).parse()
                # If some additional transformations are needed for the
                # arguments and options, do it here.
        """

        self.options, self.args = self.parser.parse_args(self.args[1:])

        # process tags
        if hasattr(self.options, 'tags') and not self.options.tags:
            # optparse defaults does not do what's expected
            self.options.tags = ['all']
        if hasattr(self.options, 'tags') and self.options.tags:
            if not C.MERGE_MULTIPLE_CLI_TAGS:
                if len(self.options.tags) > 1:
                    display.deprecated('Specifying --tags multiple times on the command line currently uses the last specified value. '
                                       'In 2.4, values will be merged instead.  Set merge_multiple_cli_tags=True in ansible.cfg to get this behavior now.',
                                       version=2.5, removed=False)
                    self.options.tags = [self.options.tags[-1]]

            tags = set()
            for tag_set in self.options.tags:
                for tag in tag_set.split(u','):
                    tags.add(tag.strip())
            self.options.tags = list(tags)

        # process skip_tags
        if hasattr(self.options, 'skip_tags') and self.options.skip_tags:
            if not C.MERGE_MULTIPLE_CLI_TAGS:
                if len(self.options.skip_tags) > 1:
                    display.deprecated('Specifying --skip-tags multiple times on the command line currently uses the last specified value. '
                                       'In 2.4, values will be merged instead.  Set merge_multiple_cli_tags=True in ansible.cfg to get this behavior now.',
                                       version=2.5, removed=False)
                    self.options.skip_tags = [self.options.skip_tags[-1]]

            skip_tags = set()
            for tag_set in self.options.skip_tags:
                for tag in tag_set.split(u','):
                    skip_tags.add(tag.strip())
            self.options.skip_tags = list(skip_tags)

        # process inventory options except for CLIs that require their own processing
        if hasattr(self.options, 'inventory') and not self.SKIP_INVENTORY_DEFAULTS:

            if self.options.inventory:

                # should always be list
                if isinstance(self.options.inventory, string_types):
                    self.options.inventory = [self.options.inventory]

                # Ensure full paths when needed
                self.options.inventory = [unfrackpath(opt, follow=False) if ',' not in opt else opt for opt in self.options.inventory]
            else:
                self.options.inventory = C.DEFAULT_HOST_LIST

    @staticmethod
    def version(prog):
        ''' return ansible version '''
        result = "{0} {1}".format(prog, __version__)
        gitinfo = CLI._gitinfo()
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

    @staticmethod
    def version_info(gitinfo=False):
        ''' return full ansible version info '''
        if gitinfo:
            # expensive call, user with care
            ansible_version_string = CLI.version('')
        else:
            ansible_version_string = __version__
        ansible_version = ansible_version_string.split()[0]
        ansible_versions = ansible_version.split('.')
        for counter in range(len(ansible_versions)):
            if ansible_versions[counter] == "":
                ansible_versions[counter] = 0
            try:
                ansible_versions[counter] = int(ansible_versions[counter])
            except Exception:
                pass
        if len(ansible_versions) < 3:
            for counter in range(len(ansible_versions), 3):
                ansible_versions.append(0)
        return {'string': ansible_version_string.strip(),
                'full': ansible_version,
                'major': ansible_versions[0],
                'minor': ansible_versions[1],
                'revision': ansible_versions[2]}

    @staticmethod
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
            line = f.readline().rstrip("\n")
            if line.startswith("ref:"):
                branch_path = os.path.join(repo_path, line[5:])
            else:
                branch_path = None
            f.close()
            if branch_path and os.path.exists(branch_path):
                branch = '/'.join(line.split('/')[2:])
                f = open(branch_path)
                commit = f.readline()[:10]
                f.close()
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

    @staticmethod
    def _gitinfo():
        basedir = os.path.join(os.path.dirname(__file__), '..', '..', '..')
        repo_path = os.path.join(basedir, '.git')
        result = CLI._git_repo_info(repo_path)
        submodules = os.path.join(basedir, '.gitmodules')
        if not os.path.exists(submodules):
            return result
        f = open(submodules)
        for line in f:
            tokens = line.strip().split(' ')
            if tokens[0] == 'path':
                submodule_path = tokens[2]
                submodule_info = CLI._git_repo_info(os.path.join(basedir, submodule_path, '.git'))
                if not submodule_info:
                    submodule_info = ' not found - use git submodule update --init ' + submodule_path
                result += "\n  {0}: {1}".format(submodule_path, submodule_info)
        f.close()
        return result

    def pager(self, text):
        ''' find reasonable way to display text '''
        # this is a much simpler form of what is in pydoc.py
        if not sys.stdout.isatty():
            display.display(text, screen_only=True)
        elif 'PAGER' in os.environ:
            if sys.platform == 'win32':
                display.display(text, screen_only=True)
            else:
                self.pager_pipe(text, os.environ['PAGER'])
        else:
            p = subprocess.Popen('less --version', shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            p.communicate()
            if p.returncode == 0:
                self.pager_pipe(text, 'less')
            else:
                display.display(text, screen_only=True)

    @staticmethod
    def pager_pipe(text, cmd):
        ''' pipe text through a pager '''
        if 'LESS' not in os.environ:
            os.environ['LESS'] = CLI.LESS_OPTS
        try:
            cmd = subprocess.Popen(cmd, shell=True, stdin=subprocess.PIPE, stdout=sys.stdout)
            cmd.communicate(input=to_bytes(text))
        except IOError:
            pass
        except KeyboardInterrupt:
            pass

    @classmethod
    def tty_ify(cls, text):

        t = cls._ITALIC.sub("`" + r"\1" + "'", text)    # I(word) => `word'
        t = cls._BOLD.sub("*" + r"\1" + "*", t)         # B(word) => *word*
        t = cls._MODULE.sub("[" + r"\1" + "]", t)       # M(word) => [word]
        t = cls._URL.sub(r"\1", t)                      # U(word) => word
        t = cls._CONST.sub("`" + r"\1" + "'", t)        # C(word) => `word'

        return t

    @staticmethod
    def _play_prereqs(options):

        # all needs loader
        loader = DataLoader()

        basedir = getattr(options, 'basedir', False)
        if basedir:
            loader.set_basedir(basedir)

        vault_ids = options.vault_ids
        default_vault_ids = C.DEFAULT_VAULT_IDENTITY_LIST
        vault_ids = default_vault_ids + vault_ids

        vault_secrets = CLI.setup_vault_secrets(loader,
                                                vault_ids=vault_ids,
                                                vault_password_files=options.vault_password_files,
                                                ask_vault_pass=options.ask_vault_pass,
                                                auto_prompt=False)
        loader.set_vault_secrets(vault_secrets)

        # create the inventory, and filter it based on the subset specified (if any)
        inventory = InventoryManager(loader=loader, sources=options.inventory)

        # create the variable manager, which will be shared throughout
        # the code, ensuring a consistent view of global variables
        variable_manager = VariableManager(loader=loader, inventory=inventory)

        if hasattr(options, 'basedir'):
            if options.basedir:
                variable_manager.safe_basedir = True
        else:
            variable_manager.safe_basedir = True

        # load vars from cli options
        variable_manager.extra_vars = load_extra_vars(loader=loader, options=options)
        variable_manager.options_vars = load_options_vars(options, CLI.version_info(gitinfo=False))

        return loader, inventory, variable_manager

    @staticmethod
    def get_host_list(inventory, subset, pattern='all'):

        no_hosts = False
        if len(inventory.list_hosts()) == 0:
            # Empty inventory
            if C.LOCALHOST_WARNING:
                display.warning("provided hosts list is empty, only localhost is available. Note that the implicit localhost does not match 'all'")
            no_hosts = True

        inventory.subset(subset)

        hosts = inventory.list_hosts(pattern)
        if len(hosts) == 0 and no_hosts is False:
            raise AnsibleError("Specified hosts and/or --limit does not match any hosts")

        return hosts
