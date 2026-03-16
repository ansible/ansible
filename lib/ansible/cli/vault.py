#!/usr/bin/env python
# (c) 2014, James Tanner <tanner.jc@gmail.com>
# Copyright: (c) 2018, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
# PYTHON_ARGCOMPLETE_OK

from __future__ import annotations

# ansible.cli needs to be imported first, to ensure the source bin/* scripts run that code first
from ansible.cli import CLI

import os
import sys

from ansible import constants as C
from ansible import context
from ansible.cli.arguments import option_helpers as opt_help
from ansible.errors import AnsibleOptionsError
from ansible.module_utils.common.text.converters import to_text, to_bytes
from ansible.parsing.dataloader import DataLoader
from ansible.parsing.vault import VaultEditor, VaultLib, match_encrypt_secret
from ansible.utils.display import Display

display = Display()


class VaultCLI(CLI):
    """ can encrypt any structured data file used by Ansible.
    This can include *group_vars/* or *host_vars/* inventory variables,
    variables loaded by *include_vars* or *vars_files*, or variable files
    passed on the ansible-playbook command line with *-e @file.yml* or *-e @file.json*.
    Role variables and defaults are also included!

    Because Ansible tasks, handlers, and other objects are data, these can also be encrypted with vault.
    If you'd like to not expose what variables you are using, you can keep an individual task file entirely encrypted.
    """

    name = 'ansible-vault'

    FROM_STDIN = "stdin"
    FROM_ARGS = "the command line args"
    FROM_PROMPT = "the interactive prompt"

    def __init__(self, args):

        self.b_vault_pass = None
        self.b_new_vault_pass = None
        self.encrypt_string_read_stdin = False

        self.encrypt_secret = None
        self.encrypt_vault_id = None
        self.new_encrypt_secret = None
        self.new_encrypt_vault_id = None

        super(VaultCLI, self).__init__(args)

    def init_parser(self):
        super(VaultCLI, self).init_parser(
            desc="encryption/decryption utility for Ansible data files",
            epilog="\nSee '%s <command> --help' for more information on a specific command.\n\n" % os.path.basename(sys.argv[0])
        )

        common = opt_help.ArgumentParser(add_help=False)
        opt_help.add_vault_options(common)
        opt_help.add_verbosity_options(common)

        subparsers = self.parser.add_subparsers(dest='action')
        subparsers.required = True

        output = opt_help.ArgumentParser(add_help=False)
        output.add_argument('--output', default=None, dest='output_file',
                            help='output file name for encrypt or decrypt; use - for stdout',
                            type=opt_help.unfrack_path())

        # For encrypting actions, we can also specify which of multiple vault ids should be used for encrypting
        vault_id = opt_help.ArgumentParser(add_help=False)
        vault_id.add_argument('--encrypt-vault-id', default=[], dest='encrypt_vault_id',
                              action='store', type=str,
                              help='the vault id used to encrypt (required if more than one vault-id is provided)')

        create_parser = subparsers.add_parser('create', help='Create new vault encrypted file', parents=[vault_id, common])
        create_parser.set_defaults(func=self.execute_create)
        create_parser.add_argument('args', help='Filename', metavar='file_name', nargs='*')
        create_parser.add_argument('--skip-tty-check', default=False, help='allows editor to be opened when no tty attached',
                                   dest='skip_tty_check', action='store_true')

        decrypt_parser = subparsers.add_parser('decrypt', help='Decrypt vault encrypted file or string', parents=[output, common])
        decrypt_parser.set_defaults(func=self.execute_decrypt)
        decrypt_parser.add_argument('args', help='Filename', metavar='file_name', nargs='*')

        edit_parser = subparsers.add_parser('edit', help='Edit vault encrypted file', parents=[vault_id, common])
        edit_parser.set_defaults(func=self.execute_edit)
        edit_parser.add_argument('args', help='Filename', metavar='file_name', nargs='*')

        view_parser = subparsers.add_parser('view', help='View vault encrypted file', parents=[common])
        view_parser.set_defaults(func=self.execute_view)
        view_parser.add_argument('args', help='Filename', metavar='file_name', nargs='*')

        encrypt_parser = subparsers.add_parser('encrypt', help='Encrypt YAML file', parents=[common, output, vault_id])
        encrypt_parser.set_defaults(func=self.execute_encrypt)
        encrypt_parser.add_argument('args', help='Filename', metavar='file_name', nargs='*')

        enc_str_parser = subparsers.add_parser('encrypt_string', help='Encrypt a string', parents=[common, output, vault_id])
        enc_str_parser.set_defaults(func=self.execute_encrypt_string)
        enc_str_parser.add_argument('args', help='String to encrypt', metavar='string_to_encrypt', nargs='*')
        enc_str_parser.add_argument('-p', '--prompt', dest='encrypt_string_prompt',
                                    action='store_true',
                                    help="Prompt for the string to encrypt")
        enc_str_parser.add_argument('--show-input', dest='show_string_input', default=False, action='store_true',
                                    help='Do not hide input when prompted for the string to encrypt')
        enc_str_parser.add_argument('-n', '--name', dest='encrypt_string_names',
                                    action='append',
                                    help="Specify the variable name")
        enc_str_parser.add_argument('--stdin-name', dest='encrypt_string_stdin_name',
                                    default=None,
                                    help="Specify the variable name for stdin")

        rekey_parser = subparsers.add_parser('rekey', help='Re-key a vault encrypted file', parents=[common, vault_id])
        rekey_parser.set_defaults(func=self.execute_rekey)
        rekey_new_group = rekey_parser.add_mutually_exclusive_group()
        rekey_new_group.add_argument('--new-vault-password-file', default=None, dest='new_vault_password_file',
                                     help="new vault password file for rekey", type=opt_help.unfrack_path())
        rekey_new_group.add_argument('--new-vault-id', default=None, dest='new_vault_id', type=str,
                                     help='the new vault identity to use for rekey')
        rekey_parser.add_argument('args', help='Filename', metavar='file_name', nargs='*')

    def post_process_args(self, options):
        options = super(VaultCLI, self).post_process_args(options)

        display.verbosity = options.verbosity

        if options.vault_ids:
            for vault_id in options.vault_ids:
                if u';' in vault_id:
                    raise AnsibleOptionsError("'%s' is not a valid vault id. The character ';' is not allowed in vault ids" % vault_id)

        if getattr(options, 'output_file', None) and len(options.args) > 1:
            raise AnsibleOptionsError("At most one input file may be used with the --output option")

        if options.action == 'encrypt_string':
            if '-' in options.args or options.encrypt_string_stdin_name or (not options.args and not options.encrypt_string_prompt):
                # prompting from stdin and reading from stdin are mutually exclusive, if stdin is still provided, it is ignored
                self.encrypt_string_read_stdin = True

            if options.encrypt_string_prompt and self.encrypt_string_read_stdin:
                # should only trigger if prompt + either - or encrypt string stdin name were provided
                raise AnsibleOptionsError('The --prompt option is not supported if also reading input from stdin')

        return options

    def run(self):
        super(VaultCLI, self).run()
        loader = DataLoader()

        # set default restrictive umask
        old_umask = os.umask(0o077)

        vault_ids = list(context.CLIARGS['vault_ids'])

        # there are 3 types of actions, those that just 'read' (decrypt, view) and only
        # need to ask for a password once, and those that 'write' (create, encrypt) that
        # ask for a new password and confirm it, and 'read/write (rekey) that asks for the
        # old password, then asks for a new one and confirms it.

        default_vault_ids = C.DEFAULT_VAULT_IDENTITY_LIST
        vault_ids = default_vault_ids + vault_ids

        action = context.CLIARGS['action']

        # TODO: instead of prompting for these before, we could let VaultEditor
        #       call a callback when it needs it.
        if action in ['decrypt', 'view', 'rekey', 'edit']:
            vault_secrets = self.setup_vault_secrets(loader, vault_ids=vault_ids,
                                                     vault_password_files=list(context.CLIARGS['vault_password_files']),
                                                     ask_vault_pass=context.CLIARGS['ask_vault_pass'])
            if not vault_secrets:
                raise AnsibleOptionsError("A vault password is required to use Ansible's Vault")

        if action in ['encrypt', 'encrypt_string', 'create']:

            encrypt_vault_id = None
            # no --encrypt-vault-id context.CLIARGS['encrypt_vault_id'] for 'edit'
            if action not in ['edit']:
                encrypt_vault_id = context.CLIARGS['encrypt_vault_id'] or C.DEFAULT_VAULT_ENCRYPT_IDENTITY

            vault_secrets = None
            vault_secrets = \
                self.setup_vault_secrets(loader,
                                         vault_ids=vault_ids,
                                         vault_password_files=list(context.CLIARGS['vault_password_files']),
                                         ask_vault_pass=context.CLIARGS['ask_vault_pass'],
                                         create_new_password=True)

            if len(vault_secrets) > 1 and not encrypt_vault_id:
                raise AnsibleOptionsError("The vault-ids %s are available to encrypt. Specify the vault-id to encrypt with --encrypt-vault-id" %
                                          ','.join([x[0] for x in vault_secrets]))

            if not vault_secrets:
                raise AnsibleOptionsError("A vault password is required to use Ansible's Vault")

            encrypt_secret = match_encrypt_secret(vault_secrets,
                                                  encrypt_vault_id=encrypt_vault_id)

            # only one secret for encrypt for now, use the first vault_id and use its first secret
            # TODO: exception if more than one?
            self.encrypt_vault_id = encrypt_secret[0]
            self.encrypt_secret = encrypt_secret[1]

        if action in ['rekey']:
            encrypt_vault_id = context.CLIARGS['encrypt_vault_id'] or C.DEFAULT_VAULT_ENCRYPT_IDENTITY
            # print('encrypt_vault_id: %s' % encrypt_vault_id)
            # print('default_encrypt_vault_id: %s' % default_encrypt_vault_id)

            # new_vault_ids should only ever be one item, from
            # load the default vault ids if we are using encrypt-vault-id
            new_vault_ids = []
            if encrypt_vault_id:
                new_vault_ids = default_vault_ids
            if context.CLIARGS['new_vault_id']:
                new_vault_ids.append(context.CLIARGS['new_vault_id'])

            new_vault_password_files = []
            if context.CLIARGS['new_vault_password_file']:
                new_vault_password_files.append(context.CLIARGS['new_vault_password_file'])

            new_vault_secrets = \
                self.setup_vault_secrets(loader,
                                         vault_ids=new_vault_ids,
                                         vault_password_files=new_vault_password_files,
                                         ask_vault_pass=context.CLIARGS['ask_vault_pass'],
                                         initialize_context=False,
                                         create_new_password=True)

            if not new_vault_secrets:
                raise AnsibleOptionsError("A new vault password is required to use Ansible's Vault rekey")

            # There is only one new_vault_id currently and one new_vault_secret, or we
            # use the id specified in --encrypt-vault-id
            new_encrypt_secret = match_encrypt_secret(new_vault_secrets,
                                                      encrypt_vault_id=encrypt_vault_id)

            self.new_encrypt_vault_id = new_encrypt_secret[0]
            self.new_encrypt_secret = new_encrypt_secret[1]

        loader.set_vault_secrets(vault_secrets)

        # FIXME: do we need to create VaultEditor here? its not reused
        vault = VaultLib(vault_secrets)
        self.editor = VaultEditor(vault)

        context.CLIARGS['func']()

        # and restore umask
        os.umask(old_umask)

    def execute_encrypt(self):
        """ encrypt the supplied file using the provided vault secret """

        if not context.CLIARGS['args'] and sys.stdin.isatty():
            display.display("Reading plaintext input from stdin", stderr=True)

        for f in context.CLIARGS['args'] or ['-']:
            # FIXME: use the correct vau
            self.editor.encrypt_file(f, self.encrypt_secret,
                                     vault_id=self.encrypt_vault_id,
                                     output_file=context.CLIARGS['output_file'])

        if sys.stdout.isatty():
            display.display("Encryption successful", stderr=True)

    @staticmethod
    def format_ciphertext_yaml(b_ciphertext, indent=None, name=None):
        indent = indent or 10

        block_format_var_name = ""
        if name:
            block_format_var_name = "%s: " % name

        block_format_header = "%s!vault |" % block_format_var_name
        lines = []
        vault_ciphertext = to_text(b_ciphertext)

        lines.append(block_format_header)
        for line in vault_ciphertext.splitlines():
            lines.append('%s%s' % (' ' * indent, line))

        yaml_ciphertext = '\n'.join(lines)
        return yaml_ciphertext

    def execute_encrypt_string(self):
        """ encrypt the supplied string using the provided vault secret """
        b_plaintext = None

        # Holds tuples (the_text, the_source_of_the_string, the variable name if its provided).
        b_plaintext_list = []

        # remove the non-option '-' arg (used to indicate 'read from stdin') from the candidate args so
        # we don't add it to the plaintext list
        args = [x for x in context.CLIARGS['args'] if x != '-']

        # We can prompt and read input, or read from stdin, but not both.
        if context.CLIARGS['encrypt_string_prompt']:
            msg = "String to encrypt: "

            name = None
            name_prompt_response = display.prompt('Variable name (enter for no name): ')

            # TODO: enforce var naming rules?
            if name_prompt_response != "":
                name = name_prompt_response

            # TODO: could prompt for which vault_id to use for each plaintext string
            #       currently, it will just be the default
            hide_input = not context.CLIARGS['show_string_input']
            if hide_input:
                msg = "String to encrypt (hidden): "
            else:
                msg = "String to encrypt:"

            prompt_response = display.prompt(msg, private=hide_input)

            if prompt_response == '':
                raise AnsibleOptionsError('The plaintext provided from the prompt was empty, not encrypting')

            b_plaintext = to_bytes(prompt_response)
            b_plaintext_list.append((b_plaintext, self.FROM_PROMPT, name))

        # read from stdin
        if self.encrypt_string_read_stdin:
            if sys.stdout.isatty():
                display.display("Reading plaintext input from stdin. (ctrl-d to end input, twice if your content does not already have a newline)", stderr=True)

            stdin_text = sys.stdin.read()
            if stdin_text == '':
                raise AnsibleOptionsError('stdin was empty, not encrypting')

            if sys.stdout.isatty() and not stdin_text.endswith("\n"):
                display.display("\n")

            b_plaintext = to_bytes(stdin_text)

            # defaults to None
            name = context.CLIARGS['encrypt_string_stdin_name']
            b_plaintext_list.append((b_plaintext, self.FROM_STDIN, name))

        # use any leftover args as strings to encrypt
        # Try to match args up to --name options
        if context.CLIARGS.get('encrypt_string_names', False):
            name_and_text_list = list(zip(context.CLIARGS['encrypt_string_names'], args))

            # Some but not enough --name's to name each var
            if len(args) > len(name_and_text_list):
                # Trying to avoid ever showing the plaintext in the output, so this warning is vague to avoid that.
                display.display('The number of --name options do not match the number of args.',
                                stderr=True)
                display.display('The last named variable will be "%s". The rest will not have'
                                ' names.' % context.CLIARGS['encrypt_string_names'][-1],
                                stderr=True)

            # Add the rest of the args without specifying a name
            for extra_arg in args[len(name_and_text_list):]:
                name_and_text_list.append((None, extra_arg))

        # if no --names are provided, just use the args without a name.
        else:
            name_and_text_list = [(None, x) for x in args]

        # Convert the plaintext text objects to bytestrings and collect
        for name_and_text in name_and_text_list:
            name, plaintext = name_and_text

            if plaintext == '':
                raise AnsibleOptionsError('The plaintext provided from the command line args was empty, not encrypting')

            b_plaintext = to_bytes(plaintext)
            b_plaintext_list.append((b_plaintext, self.FROM_ARGS, name))

        # TODO: specify vault_id per string?
        # Format the encrypted strings and any corresponding stderr output
        outputs = self._format_output_vault_strings(b_plaintext_list, vault_id=self.encrypt_vault_id)

        b_outs = []
        for output in outputs:
            err = output.get('err', None)
            out = output.get('out', '')
            if err:
                sys.stderr.write(err)
            b_outs.append(to_bytes(out))

        # The output must end with a newline to play nice with terminal representation.
        # Refs:
        # * https://stackoverflow.com/a/729795/595220
        # * https://github.com/ansible/ansible/issues/78932
        b_outs.append(b'')
        self.editor.write_data(b'\n'.join(b_outs), context.CLIARGS['output_file'] or '-')

        if sys.stdout.isatty():
            display.display("Encryption successful", stderr=True)

        # TODO: offer block or string ala eyaml

    def _format_output_vault_strings(self, b_plaintext_list, vault_id=None):
        # If we are only showing one item in the output, we don't need to included commented
        # delimiters in the text
        show_delimiter = False
        if len(b_plaintext_list) > 1:
            show_delimiter = True

        # list of dicts {'out': '', 'err': ''}
        output = []

        # Encrypt the plaintext, and format it into a yaml block that can be pasted into a playbook.
        # For more than one input, show some differentiating info in the stderr output so we can tell them
        # apart. If we have a var name, we include that in the yaml
        for index, b_plaintext_info in enumerate(b_plaintext_list):
            # (the text itself, which input it came from, its name)
            b_plaintext, src, name = b_plaintext_info

            b_ciphertext = self.editor.encrypt_bytes(b_plaintext, self.encrypt_secret, vault_id=vault_id)

            # block formatting
            yaml_text = self.format_ciphertext_yaml(b_ciphertext, name=name)

            err_msg = None
            if show_delimiter:
                human_index = index + 1
                if name:
                    err_msg = '# The encrypted version of variable ("%s", the string #%d from %s).\n' % (name, human_index, src)
                else:
                    err_msg = '# The encrypted version of the string #%d from %s.)\n' % (human_index, src)
            output.append({'out': yaml_text, 'err': err_msg})

        return output

    def execute_decrypt(self):
        """ decrypt the supplied file using the provided vault secret """

        if not context.CLIARGS['args'] and sys.stdin.isatty():
            display.display("Reading ciphertext input from stdin", stderr=True)

        for f in context.CLIARGS['args'] or ['-']:
            self.editor.decrypt_file(f, output_file=context.CLIARGS['output_file'])

        if sys.stdout.isatty():
            display.display("Decryption successful", stderr=True)

    def execute_create(self):
        """ create and open a file in an editor that will be encrypted with the provided vault secret when closed"""

        if len(context.CLIARGS['args']) != 1:
            raise AnsibleOptionsError("ansible-vault create can take only one filename argument")

        if sys.stdout.isatty() or context.CLIARGS['skip_tty_check']:
            self.editor.create_file(context.CLIARGS['args'][0], self.encrypt_secret,
                                    vault_id=self.encrypt_vault_id)
        else:
            raise AnsibleOptionsError("not a tty, editor cannot be opened")

    def execute_edit(self):
        """ open and decrypt an existing vaulted file in an editor, that will be encrypted again when closed"""
        for f in context.CLIARGS['args']:
            self.editor.edit_file(f)

    def execute_view(self):
        """ open, decrypt and view an existing vaulted file using a pager using the supplied vault secret """

        for f in context.CLIARGS['args']:
            # Note: vault should return byte strings because it could encrypt
            # and decrypt binary files.  We are responsible for changing it to
            # unicode here because we are displaying it and therefore can make
            # the decision that the display doesn't have to be precisely what
            # the input was (leave that to decrypt instead)
            plaintext = self.editor.plaintext(f)
            self.pager(to_text(plaintext))

    def execute_rekey(self):
        """ re-encrypt a vaulted file with a new secret, the previous secret is required """
        for f in context.CLIARGS['args']:
            # FIXME: plumb in vault_id, use the default new_vault_secret for now
            self.editor.rekey_file(f, self.new_encrypt_secret,
                                   self.new_encrypt_vault_id)

        display.display("Rekey successful", stderr=True)


def main(args=None):
    VaultCLI.cli_executor(args)


if __name__ == '__main__':
    main()
