Vault
=====

.. contents:: Topics

New in Ansible 1.5, "Vault" is a feature of ansible that allows keeping sensitive data such as passwords or keys in encrypted files, rather than as plaintext in your playbooks or roles. These vault files can then be distributed or placed in source control.

To enable this feature, a command line tool, `ansible-vault` is used to edit files, and a command line flag `--ask-vault-pass` or `--vault-password-file` is used. Alternately, you may specify the location of a password file or command Ansible to always prompt for the password in your ansible.cfg file. These options require no command line flag usage.

For best practices advice, refer to :ref:`best_practices_for_variables_and_vaults`.


.. _what_can_be_encrypted_with_vault:

What Can Be Encrypted With Vault
````````````````````````````````

The vault feature can encrypt any structured data file used by Ansible.  This can include "group_vars/" or "host_vars/" inventory variables, variables loaded by "include_vars" or "vars_files", or variable files passed on the ansible-playbook command line with "-e @file.yml" or "-e @file.json".  Role variables and defaults are also included!

Ansible tasks, handlers, and so on are also data so these can be encrypted with vault as well. To hide the names of variables that you're using, you can encrypt the task files in their entirety. However, that might be a little too much and could annoy your coworkers :)

+The vault feature can also encrypt arbitrary files, even binary files.  If a vault-encrypted file is given as the `src` argument to the `copy`, `template`, `unarchive`, `script` or `assemble` modules, the file will be placed at the destination on the target host decrypted (assuming a valid vault password is supplied when running the play).

As of version 2.3, Ansible also supports encrypting single values inside a YAML file, using the `!vault` tag to let YAML and Ansible know it uses special processing. This feature is covered in more details below.


.. _creating_files:

Creating Encrypted Files
````````````````````````

To create a new encrypted data file, run the following command::

   ansible-vault create foo.yml

First you will be prompted for a password.  The password used with vault currently must be the same for all files you wish to use together at the same time.

After providing a password, the tool will launch whatever editor you have defined with $EDITOR, and defaults to vi (before 2.1 the default was vim).  Once you are done with the editor session, the file will be saved as encrypted data.

The default cipher is AES (which is shared-secret based).


.. _editing_encrypted_files:

Editing Encrypted Files
```````````````````````

To edit an encrypted file in place, use the `ansible-vault edit` command.
This command will decrypt the file to a temporary file and allow you to edit
the file, saving it back when done and removing the temporary file::

   ansible-vault edit foo.yml


.. _rekeying_files:

Rekeying Encrypted Files
````````````````````````

Should you wish to change your password on a vault-encrypted file or files, you can do so with the rekey command::

    ansible-vault rekey foo.yml bar.yml baz.yml

This command can rekey multiple data files at once and will ask for the original
password and also the new password.


.. _encrypting_files:

Encrypting Unencrypted Files
````````````````````````````

If you have existing files that you wish to encrypt, use the `ansible-vault encrypt` command.  This command can operate on multiple files at once::

   ansible-vault encrypt foo.yml bar.yml baz.yml


.. _decrypting_files:

Decrypting Encrypted Files
``````````````````````````

If you have existing files that you no longer want to keep encrypted, you can permanently decrypt them by running the `ansible-vault decrypt` command.  This command will save them unencrypted to the disk, so be sure you do not want `ansible-vault edit` instead::

    ansible-vault decrypt foo.yml bar.yml baz.yml


.. _viewing_files:

Viewing Encrypted Files
```````````````````````

*Available since Ansible 1.8*

If you want to view the contents of an encrypted file without editing it, you can use the `ansible-vault view` command::

    ansible-vault view foo.yml bar.yml baz.yml


.. _encrypt_string_for_use_in_yaml:

Use encrypt_string to create encrypted variables to embed in yaml
`````````````````````````````````````````````````````````````````

The `ansible-vault encrypt_string` command will encrypt and format a provided string into a format
that can be included in `ansible-playbook` YAML files.

See `_single_encrypted_variable` for an example.


.. _speeding_up_vault:

Speeding Up Vault Operations
````````````````````````````

By default, Ansible uses PyCrypto to encrypt and decrypt vault files. If you have many encrypted files, decrypting them at startup may cause a perceptible delay. To speed this up, install the cryptography package::

    pip install cryptography


.. _vault_format:

Vault Format
````````````

A vault encrypted file is a UTF-8 encoded txt file.

The file format includes a new line terminated header.

For example::

    $ANSIBLE_VAULT;1.1;AES256


The header contains the vault format id, the vault format version, and a cipher id, seperated by semi-colons ';'

The first field ``$ANSIBLE_VAULT`` is the format id. Currently ``$ANSIBLE_VAULT`` is the only valid file format id. This is used to identify files that are vault encrypted (via vault.is_encrypted_file()).

The second field (`1.1`) is the vault format version. All supported versions of ansible will currently default to '1.1'.

The '1.0' format is supported for reading only (and will be converted automatically to the '1.1' format on write). The format version is currently used as an exact string compare only (version numbers are not currently 'compared').

The third field (``AES256``) identifies the cipher algorithmn used to encrypt the data. Currently, the only supported cipher is 'AES256'. [vault format 1.0 used 'AES', but current code always uses 'AES256']

Note: In the future, the header could change. Anything after the vault id and version can be considered to depend on the vault format version. This includes the cipher id, and any additional fields that could be after that.

The rest of the content of the file is the 'vaulttext'. The vaulttext is a text armored version of the
encrypted ciphertext. Each line will be 80 characters wide, except for the last line which may be shorter.

Vault Payload Format 1.1
````````````````````````

The vaulttext is a concatenation of the ciphertext and a SHA256 digest with the result 'hexlifyied'.

'hexlify' refers to the hexlify() method of pythons binascii module.

hexlify()'ied result of:

- hexlify()'ed string of the salt, followed by a newline ('\n')
- hexlify()'ed string of the crypted HMAC, followed by a newline. The HMAC is:

  - a `RFC2104 <https://www.ietf.org/rfc/rfc2104.txt>` style HMAC

    - inputs are:

      - The AES256 encrypted ciphertext
      - A PBKDF2 key. This key, the cipher key, and the cipher iv are generated from:

        - the salt, in bytes
        - 10000 iterations
        - SHA256() algorithmn
        - the first 32 bytes are the cipher key
        - the second 32 bytes are the HMAC key
        - remaining 16 bytes are the cipher iv

  -  hexlify()'ed string of the ciphertext. The ciphertext is:

    - AES256 encrypted data. The data is encrypted using:

      - AES-CTR stream cipher
      - b_pkey1
      - iv
      - a 128 bit counter block seeded from an integer iv
      - the plaintext

        - the original plaintext
        - padding up to the AES256 blocksize. (The data used for padding is based on `RFX5652 <https://tools.ietf.org/html/rfc5652#section-6.3>`)


