# Copyright: (c) 2012-2014, Michael DeHaan <michael.dehaan@gmail.com>
# Copyright: (c) 2016, Toshio Kuratomi <tkuratomi@ansible.com>
# Copyright: (c) 2018, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import annotations

import locale
import os
import sys

# We overload the ``ansible`` adhoc command to provide the functionality for
# ``SSH_ASKPASS``. This code is here, and not in ``adhoc.py`` to bypass
# unnecessary code. The program provided to ``SSH_ASKPASS`` can only be invoked
# as a singular command, ``python -m`` doesn't work for that use case, and we
# aren't adding a new entrypoint at this time. Assume that if we are executing
# and there is only a single item in argv plus the executable, and the env var
# is set we are in ``SSH_ASKPASS`` mode
if 1 <= len(sys.argv) <= 2 and os.path.basename(sys.argv[0]) == "ansible" and os.getenv('_ANSIBLE_SSH_ASKPASS_SHM'):
    from ansible.cli import _ssh_askpass
    _ssh_askpass.main()


# Used for determining if the system is running a new enough python version
# and should only restrict on our documented minimum versions
_PY_MIN = (3, 12)

if sys.version_info < _PY_MIN:
    raise SystemExit(
        f"ERROR: Ansible requires Python {'.'.join(map(str, _PY_MIN))} or newer on the controller. "
        f"Current version: {''.join(sys.version.splitlines())}"
    )


def check_blocking_io():
    """Check stdin/stdout/stderr to make sure they are using blocking IO."""
    handles = []

    for handle in (sys.stdin, sys.stdout, sys.stderr):
        # noinspection PyBroadException
        try:
            fd = handle.fileno()
        except Exception:
            continue  # not a real file handle, such as during the import sanity test

        if not os.get_blocking(fd):
            handles.append(getattr(handle, 'name', None) or '#%s' % fd)

    if handles:
        raise SystemExit('ERROR: Ansible requires blocking IO on stdin/stdout/stderr. '
                         'Non-blocking file handles detected: %s' % ', '.join(_io for _io in handles))


check_blocking_io()


def initialize_locale():
    """Set the locale to the users default setting and ensure
    the locale and filesystem encoding are UTF-8.
    """
    try:
        locale.setlocale(locale.LC_ALL, '')
        dummy, encoding = locale.getlocale()
    except (locale.Error, ValueError) as e:
        raise SystemExit(
            'ERROR: Ansible could not initialize the preferred locale: %s' % e
        )

    if not encoding or encoding.lower() not in ('utf-8', 'utf8'):
        raise SystemExit('ERROR: Ansible requires the locale encoding to be UTF-8; Detected %s.' % encoding)

    fs_enc = sys.getfilesystemencoding()
    if fs_enc.lower() != 'utf-8':
        raise SystemExit('ERROR: Ansible requires the filesystem encoding to be UTF-8; Detected %s.' % fs_enc)


initialize_locale()


import getpass
import subprocess
import traceback
from abc import ABC, abstractmethod
from pathlib import Path

from ansible import _internal  # do not remove or defer; ensures controller-specific state is set early

_internal.setup()

from ansible.errors import AnsibleError, ExitCode

try:
    from ansible import constants as C
    from ansible.utils.display import Display
    display = Display()
except Exception as ex:
    if isinstance(ex, AnsibleError):
        ex_msg = ' '.join((ex.message, ex._help_text or '')).strip()
    else:
        ex_msg = str(ex)

    print(f'ERROR: {ex_msg}\n\n{"".join(traceback.format_exception(ex))}', file=sys.stderr)
    sys.exit(5)


from ansible import context
from ansible.utils import display as _display
from ansible.cli.arguments import option_helpers as opt_help
from ansible.inventory.manager import InventoryManager
from ansible.module_utils.common.text.converters import to_bytes, to_text
from ansible.module_utils.common.collections import is_sequence
from ansible.module_utils.common.file import is_executable
from ansible.parsing.dataloader import DataLoader
from ansible.parsing.vault import PromptVaultSecret, get_file_vault_secret, VaultSecretsContext
from ansible.plugins.loader import add_all_plugin_dirs, init_plugin_loader
from ansible.release import __version__
from ansible.utils.collection_loader import AnsibleCollectionConfig
from ansible.utils.collection_loader._collection_finder import _get_collection_name_from_path
from ansible.utils.path import unfrackpath
from ansible.vars.manager import VariableManager
from ansible.module_utils._internal import _deprecator
from ansible._internal._ssh import _agent_launch


try:
    import argcomplete
    HAS_ARGCOMPLETE = True
except ImportError:
    HAS_ARGCOMPLETE = False


class CLI(ABC):
    """ code behind bin/ansible* programs """

    PAGER = C.config.get_config_value('PAGER')

    # -F (quit-if-one-screen) -R (allow raw ansi control chars)
    # -S (chop long lines) -X (disable termcap init and de-init)
    LESS_OPTS = 'FRSX'
    SKIP_INVENTORY_DEFAULTS = False
    USES_CONNECTION = False

    def __init__(self, args, callback=None):
        """
        Base init method for all command line programs
        """

        if not args:
            raise ValueError('A non-empty list for args is required')

        self.args = args
        self.parser = None
        self.callback = callback

        self.show_devel_warning()

    def show_devel_warning(self) -> None:
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

        # Initialize plugin loader after parse, so that the init code can utilize parsed arguments
        cli_collections_path = context.CLIARGS.get('collections_path') or []
        if not is_sequence(cli_collections_path):
            # In some contexts ``collections_path`` is singular
            cli_collections_path = [cli_collections_path]
        init_plugin_loader(cli_collections_path)

        display.vv(to_text(opt_help.version(self.parser.prog)))

        if C.CONFIG_FILE:
            display.v(u"Using %s as config file" % to_text(C.CONFIG_FILE))
        else:
            display.v(u"No config file found; using defaults")

        _display._report_config_warnings(_deprecator.ANSIBLE_CORE_DEPRECATOR)

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
                        ask_vault_pass=None, auto_prompt=True):
        vault_password_files = vault_password_files or []
        vault_ids = vault_ids or []

        # convert vault_password_files into vault_ids slugs
        for password_file in vault_password_files:
            id_slug = u'%s@%s' % (C.DEFAULT_VAULT_IDENTITY, password_file)

            # note this makes --vault-id higher precedence than --vault-password-file
            # if we want to intertwingle them in order probably need a cli callback to populate vault_ids
            # used by --vault-id and --vault-password-file
            vault_ids.append(id_slug)

        # if an action needs an encrypt password (create_new_password=True) and we don't
        # have other secrets setup, then automatically add a password prompt as well.
        # prompts can't/shouldn't work without a tty, so don't add prompt secrets
        if ask_vault_pass or (not vault_ids and auto_prompt):

            id_slug = u'%s@%s' % (C.DEFAULT_VAULT_IDENTITY, u'prompt_ask_vault_pass')
            vault_ids.append(id_slug)

        return vault_ids

    @staticmethod
    def setup_vault_secrets(loader, vault_ids, vault_password_files=None,
                            ask_vault_pass=None, create_new_password=False,
                            auto_prompt=True, initialize_context=True):
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
                                        auto_prompt=auto_prompt)

        last_exception = found_vault_secret = None
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

                found_vault_secret = True
                vault_secrets.append((built_vault_id, prompted_vault_secret))

                # update loader with new secrets incrementally, so we can load a vault password
                # that is encrypted with a vault secret provided earlier
                loader.set_vault_secrets(vault_secrets)
                continue

            # assuming anything else is a password file
            display.vvvvv('Reading vault password file: %s' % vault_id_value)
            # read vault_pass from a file
            try:
                file_vault_secret = get_file_vault_secret(filename=vault_id_value,
                                                          vault_id=vault_id_name,
                                                          loader=loader)
            except AnsibleError as exc:
                display.warning('Error getting vault password file (%s): %s' % (vault_id_name, to_text(exc)))
                last_exception = exc
                continue

            try:
                file_vault_secret.load()
            except AnsibleError as exc:
                display.warning('Error in vault password file loading (%s): %s' % (vault_id_name, to_text(exc)))
                last_exception = exc
                continue

            found_vault_secret = True
            if vault_id_name:
                vault_secrets.append((vault_id_name, file_vault_secret))
            else:
                vault_secrets.append((C.DEFAULT_VAULT_IDENTITY, file_vault_secret))

            # update loader with as-yet-known vault secrets
            loader.set_vault_secrets(vault_secrets)

        # An invalid or missing password file will error globally
        # if no valid vault secret was found.
        if last_exception and not found_vault_secret:
            raise last_exception

        if initialize_context:
            VaultSecretsContext.initialize(VaultSecretsContext(vault_secrets))

        return vault_secrets

    @staticmethod
    def _get_secret(prompt: str) -> str:
        return getpass.getpass(prompt=prompt)

    @staticmethod
    def ask_passwords():
        """ prompt for connection and become passwords if needed """

        op = context.CLIARGS
        sshpass = None
        becomepass = None

        become_prompt_method = "BECOME" if C.AGNOSTIC_BECOME_PROMPT else op['become_method'].upper()

        try:
            become_prompt = "%s password: " % become_prompt_method
            if op['ask_pass']:
                sshpass = CLI._get_secret("SSH password: ")
                become_prompt = "%s password[defaults to SSH password]: " % become_prompt_method
            elif op['connection_password_file']:
                sshpass = CLI.get_password_from_file(op['connection_password_file'])

            if op['become_ask_pass']:
                becomepass = CLI._get_secret(become_prompt)
                if op['ask_pass'] and becomepass == '':
                    becomepass = sshpass
            elif op['become_password_file']:
                becomepass = CLI.get_password_from_file(op['become_password_file'])

        except EOFError:
            pass

        return sshpass, becomepass

    def validate_conflicts(self, op, runas_opts=False, fork_opts=False):
        """ check for conflicting options """

        if fork_opts:
            if op.forks < 1:
                self.parser.error("The number of processes (--forks) must be >= 1")

        return op

    @abstractmethod
    def init_parser(self, desc=None, epilog=None):
        """
        Create an options parser for most ansible scripts

        Subclasses need to implement this method.  They will usually call the base class's
        init_parser to create a basic version and then add their own options on top of that.

        An implementation will look something like this::

            def init_parser(self):
                super(MyCLI, self).init_parser(desc='The purpose of the program is...')
                ansible.arguments.option_helpers.add_runas_options(self.parser)
                self.parser.add_option('--my-option', dest='my_option', action='store')
        """
        self.parser = opt_help.create_base_parser(self.name, desc=desc, epilog=epilog)

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
                if isinstance(options.listofhosts, str):
                    options.listofhosts = options.listofhosts.split(',')
                return options
        """

        # process tags
        if hasattr(options, 'tags') and not options.tags:
            # optparse defaults does not do what's expected
            # More specifically, we want `--tags` to be additive. So we cannot
            # simply change C.TAGS_RUN's default to ["all"] because then passing
            # --tags foo would cause us to have ['all', 'foo']
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

        # Make sure path argument doesn't have a backslash
        if hasattr(options, 'action') and options.action in ['install', 'download'] and hasattr(options, 'args'):
            options.args = [path.rstrip("/") for path in options.args]

        # process inventory options except for CLIs that require their own processing
        if hasattr(options, 'inventory') and not self.SKIP_INVENTORY_DEFAULTS:

            if options.inventory:

                # should always be list
                if isinstance(options.inventory, str):
                    options.inventory = [options.inventory]

                # Ensure full paths when needed
                options.inventory = [unfrackpath(opt, follow=False) if ',' not in opt else opt for opt in options.inventory]
            else:
                options.inventory = C.DEFAULT_HOST_LIST

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
        except SystemExit as ex:
            if ex.code != 0:
                self.parser.exit(status=2, message=" \n%s" % self.parser.format_help())
            raise
        options = self.post_process_args(options)
        context._init_global_context(options)

    @staticmethod
    def version_info(gitinfo=False):
        """ return full ansible version info """
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
        """ find reasonable way to display text """
        # this is a much simpler form of what is in pydoc.py
        if not sys.stdout.isatty():
            display.display(text, screen_only=True)
        elif CLI.PAGER:
            if sys.platform == 'win32':
                display.display(text, screen_only=True)
            else:
                CLI.pager_pipe(text)
        else:
            p = subprocess.Popen('less --version', shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            p.communicate()
            if p.returncode == 0:
                CLI.pager_pipe(text, 'less')
            else:
                display.display(text, screen_only=True)

    @staticmethod
    def pager_pipe(text):
        """ pipe text through a pager """
        if 'less' in CLI.PAGER:
            os.environ['LESS'] = CLI.LESS_OPTS
        try:
            cmd = subprocess.Popen(CLI.PAGER, shell=True, stdin=subprocess.PIPE, stdout=sys.stdout)
            cmd.communicate(input=to_bytes(text))
        except (OSError, KeyboardInterrupt):
            pass

    def _play_prereqs(self):
        # TODO: evaluate moving all of the code that touches ``AnsibleCollectionConfig``
        # into ``init_plugin_loader`` so that we can specifically remove
        # ``AnsibleCollectionConfig.playbook_paths`` to make it immutable after instantiation

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

        if self.USES_CONNECTION:
            _agent_launch.launch_ssh_agent()

        # create the inventory, and filter it based on the subset specified (if any)
        inventory = InventoryManager(loader=loader, sources=options['inventory'], cache=(not options.get('flush_cache')))

        # create the variable manager, which will be shared throughout
        # the code, ensuring a consistent view of global variables
        variable_manager = VariableManager(loader=loader, inventory=inventory, version_info=CLI.version_info(gitinfo=False))

        # flush fact cache if requested
        if options['flush_cache']:
            CLI._flush_cache(inventory, variable_manager)

        return loader, inventory, variable_manager

    @staticmethod
    def _flush_cache(inventory, variable_manager):
        variable_manager.clear_facts('localhost')
        for host in inventory.list_hosts():
            hostname = host.get_name()
            variable_manager.clear_facts(hostname)

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
            raise AnsibleError("Specified inventory, host pattern and/or --limit leaves us with no hosts to target.")

        return hosts

    @staticmethod
    def get_password_from_file(pwd_file: str) -> str:
        b_pwd_file = to_bytes(pwd_file)

        if b_pwd_file == b'-':
            # ensure its read as bytes
            secret = sys.stdin.buffer.read()

        elif not os.path.exists(b_pwd_file):
            raise AnsibleError("The password file %s was not found" % pwd_file)

        elif is_executable(b_pwd_file):
            display.vvvv(u'The password file %s is a script.' % to_text(pwd_file))
            cmd = [b_pwd_file]

            try:
                p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            except OSError as e:
                raise AnsibleError("Problem occurred when trying to run the password script %s (%s)."
                                   " If this is not a script, remove the executable bit from the file." % (pwd_file, e))

            stdout, stderr = p.communicate()
            if p.returncode != 0:
                raise AnsibleError("The password script %s returned an error (rc=%s): %s" % (pwd_file, p.returncode, to_text(stderr)))
            secret = stdout

        else:
            try:
                with open(b_pwd_file, "rb") as password_file:
                    secret = password_file.read().strip()
            except OSError as ex:
                raise AnsibleError(f"Could not read password file {pwd_file!r}.") from ex

        secret = secret.strip(b'\r\n')

        if not secret:
            raise AnsibleError('Empty password was provided from file (%s)' % pwd_file)

        return to_text(secret)

    @classmethod
    def cli_executor(cls, args=None):
        if args is None:
            args = sys.argv

        try:
            display.debug("starting run")

            ansible_dir = Path(C.ANSIBLE_HOME).expanduser()
            try:
                ansible_dir.mkdir(mode=0o700, exist_ok=True)
            except OSError as ex:
                display.error_as_warning(f"Failed to create the directory {ansible_dir!r}.", ex)
            else:
                display.debug("Created the '%s' directory" % ansible_dir)

            cli = cls(args)
            exit_code = cli.run()
        except AnsibleError as ex:
            display.error(ex)
            exit_code = ex._exit_code
        except KeyboardInterrupt:
            display.error("User interrupted execution")
            exit_code = ExitCode.KEYBOARD_INTERRUPT
        except Exception as ex:
            try:
                raise AnsibleError("Unexpected Exception, this is probably a bug.") from ex
            except AnsibleError as ex2:
                # DTFIX-FUTURE: clean this up so we're not hacking the internals- re-wrap in an AnsibleCLIUnhandledError that always shows TB, or?
                from ansible.module_utils._internal import _traceback
                _traceback._is_traceback_enabled = lambda *_args, **_kwargs: True
                display.error(ex2)
                exit_code = ExitCode.UNKNOWN_ERROR

        sys.exit(exit_code)
