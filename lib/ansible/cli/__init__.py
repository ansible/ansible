# Copyright: (c) 2012-2014, Michael DeHaan <michael.dehaan@gmail.com>
# Copyright: (c) 2016, Toshio Kuratomi <tkuratomi@ansible.com>
# Copyright: (c) 2018, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import getpass
import os
import subprocess
import sys

from abc import ABCMeta, abstractmethod

from ansible.cli.arguments import option_helpers as opt_help
from ansible import constants as C
from ansible import context
from ansible.errors import AnsibleError
from ansible.inventory.manager import InventoryManager
from ansible.module_utils.six import with_metaclass, string_types
from ansible.module_utils._text import to_bytes, to_text
from ansible.parsing.dataloader import DataLoader
from ansible.parsing.vault import PromptVaultSecret, get_file_vault_secret
from ansible.plugins.loader import add_all_plugin_dirs
from ansible.release import __version__
from ansible.utils.collection_loader import AnsibleCollectionConfig
from ansible.utils.collection_loader._collection_finder import _get_collection_name_from_path
from ansible.utils.display import Display
from ansible.utils.path import unfrackpath
from ansible.utils.unsafe_proxy import to_unsafe_text
from ansible.vars.manager import VariableManager

try:
    import argcomplete
    HAS_ARGCOMPLETE = True
except ImportError:
    HAS_ARGCOMPLETE = False


display = Display()


class CLI(with_metaclass(ABCMeta, object)):
    ''' code behind bin/ansible* programs '''

    PAGER = 'less'

    # -F (quit-if-one-screen) -R (allow raw ansi control chars)
    # -S (chop long lines) -X (disable termcap init and de-init)
    LESS_OPTS = 'FRSX'
    SKIP_INVENTORY_DEFAULTS = False

    def __init__(self, args, callback=None):
        """
        Base init method for all command line programs
        """

        if not args:
            raise ValueError('A non-empty list for args is required')

        self.args = args
        self.parser = None
        self.callback = callback

        if C.DEVEL_WARNING and __version__.endswith('dev0'):
            display.warning(
                'You are running the development version of Ansible. You should only run Ansible from "devel" if '
                'you are modifying the Ansible engine, or trying out features under development. This is a rapidly '
                'changing source of code and can become unstable at any point.'
            )

    @abstractmethod
    def run(self):
        """Run the ansible command

        Subclasses must implement this method.  It does the actual work of
        running an Ansible command.
        """
        self.parse()

        display.vv(to_text(opt_help.version(self.parser.prog)))

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
            ver = deprecated[1].get('version')
            date = deprecated[1].get('date')
            collection_name = deprecated[1].get('collection_name')
            display.deprecated("%s option, %s%s" % (name, why, alt),
                               version=ver, date=date, collection_name=collection_name)

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

            # note this makes --vault-id higher precedence than --vault-password-file
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
                                        'Confirm new vault password (%(vault_id)s): ']
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
                # without erroring globally
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
                display.warning('Error in vault password file loading (%s): %s' % (vault_id_name, to_text(exc)))
                raise

            if vault_id_name:
                vault_secrets.append((vault_id_name, file_vault_secret))
            else:
                vault_secrets.append((C.DEFAULT_VAULT_IDENTITY, file_vault_secret))

            # update loader with as-yet-known vault secrets
            loader.set_vault_secrets(vault_secrets)

        return vault_secrets

    @staticmethod
    def ask_passwords():
        ''' prompt for connection and become passwords if needed '''

        op = context.CLIARGS
        sshpass = None
        becomepass = None
        become_prompt = ''

        become_prompt_method = "BECOME" if C.AGNOSTIC_BECOME_PROMPT else op['become_method'].upper()

        try:
            if op['ask_pass']:
                sshpass = getpass.getpass(prompt="SSH password: ")
                become_prompt = "%s password[defaults to SSH password]: " % become_prompt_method
            else:
                become_prompt = "%s password: " % become_prompt_method

            if op['become_ask_pass']:
                becomepass = getpass.getpass(prompt=become_prompt)
                if op['ask_pass'] and becomepass == '':
                    becomepass = sshpass
        except EOFError:
            pass

        # we 'wrap' the passwords to prevent templating as
        # they can contain special chars and trigger it incorrectly
        if sshpass:
            sshpass = to_unsafe_text(sshpass)
        if becomepass:
            becomepass = to_unsafe_text(becomepass)

        return (sshpass, becomepass)

    def validate_conflicts(self, op, runas_opts=False, fork_opts=False):
        ''' check for conflicting options '''

        if fork_opts:
            if op.forks < 1:
                self.parser.error("The number of processes (--forks) must be >= 1")

        return op

    @abstractmethod
    def init_parser(self, usage="", desc=None, epilog=None):
        """
        Create an options parser for most ansible scripts

        Subclasses need to implement this method.  They will usually call the base class's
        init_parser to create a basic version and then add their own options on top of that.

        An implementation will look something like this::

            def init_parser(self):
                super(MyCLI, self).init_parser(usage="My Ansible CLI", inventory_opts=True)
                ansible.arguments.option_helpers.add_runas_options(self.parser)
                self.parser.add_option('--my-option', dest='my_option', action='store')
        """
        self.parser = opt_help.create_base_parser(os.path.basename(self.args[0]), usage=usage, desc=desc, epilog=epilog, )

    @abstractmethod
    def post_process_args(self, options):
        """Process the command line args

        Subclasses need to implement this method.  This method validates and transforms the command
        line arguments.  It can be used to check whether conflicting values were given, whether filenames
        exist, etc.

        An implementation will look something like this::

            def post_process_args(self, options):
                options = super(MyCLI, self).post_process_args(options)
                if options.addition and options.subtraction:
                    raise AnsibleOptionsError('Only one of --addition and --subtraction can be specified')
                if isinstance(options.listofhosts, string_types):
                    options.listofhosts = string_types.split(',')
                return options
        """

        # process tags
        if hasattr(options, 'tags') and not options.tags:
            # optparse defaults does not do what's expected
            options.tags = ['all']
        if hasattr(options, 'tags') and options.tags:
            tags = set()
            for tag_set in options.tags:
                for tag in tag_set.split(u','):
                    tags.add(tag.strip())
            options.tags = list(tags)

        # process skip_tags
        if hasattr(options, 'skip_tags') and options.skip_tags:
            skip_tags = set()
            for tag_set in options.skip_tags:
                for tag in tag_set.split(u','):
                    skip_tags.add(tag.strip())
            options.skip_tags = list(skip_tags)

        # process inventory options except for CLIs that require their own processing
        if hasattr(options, 'inventory') and not self.SKIP_INVENTORY_DEFAULTS:

            if options.inventory:

                # should always be list
                if isinstance(options.inventory, string_types):
                    options.inventory = [options.inventory]

                # Ensure full paths when needed
                options.inventory = [unfrackpath(opt, follow=False) if ',' not in opt else opt for opt in options.inventory]
            else:
                options.inventory = C.DEFAULT_HOST_LIST

        # Dup args set on the root parser and sub parsers results in the root parser ignoring the args. e.g. doing
        # 'ansible-galaxy -vvv init' has no verbosity set but 'ansible-galaxy init -vvv' sets a level of 3. To preserve
        # back compat with pre-argparse changes we manually scan and set verbosity based on the argv values.
        if self.parser.prog in ['ansible-galaxy', 'ansible-vault'] and not options.verbosity:
            verbosity_arg = next(iter([arg for arg in self.args if arg.startswith('-v')]), None)
            if verbosity_arg:
                display.deprecated("Setting verbosity before the arg sub command is deprecated, set the verbosity "
                                   "after the sub command", "2.13", collection_name='ansible.builtin')
                options.verbosity = verbosity_arg.count('v')

        return options

    def parse(self):
        """Parse the command line args

        This method parses the command line arguments.  It uses the parser
        stored in the self.parser attribute and saves the args and options in
        context.CLIARGS.

        Subclasses need to implement two helper methods, init_parser() and post_process_args() which
        are called from this function before and after parsing the arguments.
        """
        self.init_parser()

        if HAS_ARGCOMPLETE:
            argcomplete.autocomplete(self.parser)

        try:
            options = self.parser.parse_args(self.args[1:])
        except SystemExit as e:
            if(e.code != 0):
                self.parser.exit(status=2, message=" \n%s " % self.parser.format_help())
            raise
        options = self.post_process_args(options)
        context._init_global_context(options)

    @staticmethod
    def version_info(gitinfo=False):
        ''' return full ansible version info '''
        if gitinfo:
            # expensive call, user with care
            ansible_version_string = opt_help.version()
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
    def pager(text):
        ''' find reasonable way to display text '''
        # this is a much simpler form of what is in pydoc.py
        if not sys.stdout.isatty():
            display.display(text, screen_only=True)
        elif 'PAGER' in os.environ:
            if sys.platform == 'win32':
                display.display(text, screen_only=True)
            else:
                CLI.pager_pipe(text, os.environ['PAGER'])
        else:
            p = subprocess.Popen('less --version', shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            p.communicate()
            if p.returncode == 0:
                CLI.pager_pipe(text, 'less')
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

    @staticmethod
    def _play_prereqs():
        options = context.CLIARGS

        # all needs loader
        loader = DataLoader()

        basedir = options.get('basedir', False)
        if basedir:
            loader.set_basedir(basedir)
            add_all_plugin_dirs(basedir)
            AnsibleCollectionConfig.playbook_paths = basedir
            default_collection = _get_collection_name_from_path(basedir)
            if default_collection:
                display.warning(u'running with default collection {0}'.format(default_collection))
                AnsibleCollectionConfig.default_collection = default_collection

        vault_ids = list(options['vault_ids'])
        default_vault_ids = C.DEFAULT_VAULT_IDENTITY_LIST
        vault_ids = default_vault_ids + vault_ids

        vault_secrets = CLI.setup_vault_secrets(loader,
                                                vault_ids=vault_ids,
                                                vault_password_files=list(options['vault_password_files']),
                                                ask_vault_pass=options['ask_vault_pass'],
                                                auto_prompt=False)
        loader.set_vault_secrets(vault_secrets)

        # create the inventory, and filter it based on the subset specified (if any)
        inventory = InventoryManager(loader=loader, sources=options['inventory'])

        # create the variable manager, which will be shared throughout
        # the code, ensuring a consistent view of global variables
        variable_manager = VariableManager(loader=loader, inventory=inventory, version_info=CLI.version_info(gitinfo=False))

        return loader, inventory, variable_manager

    @staticmethod
    def get_host_list(inventory, subset, pattern='all'):

        no_hosts = False
        if len(inventory.list_hosts()) == 0:
            # Empty inventory
            if C.LOCALHOST_WARNING and pattern not in C.LOCALHOST:
                display.warning("provided hosts list is empty, only localhost is available. Note that the implicit localhost does not match 'all'")
            no_hosts = True

        inventory.subset(subset)

        hosts = inventory.list_hosts(pattern)
        if not hosts and no_hosts is False:
            raise AnsibleError("Specified hosts and/or --limit does not match any hosts")

        return hosts
