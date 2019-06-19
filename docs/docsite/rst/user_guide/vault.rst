.. _vault:

Ansible Vault
=============

.. contents:: Topics

Ansible Vault is a feature of ansible that allows you to keep sensitive data such as passwords or keys in encrypted files, rather than as plaintext in playbooks or roles. These vault files can then be distributed or placed in source control.

To enable this feature, a command line tool - :ref:`ansible-vault` - is used to edit files, and a command line flag (:option:`--ask-vault-pass <ansible-playbook --ask-vault-pass>`, :option:`--vault-password-file <ansible-playbook --vault-password-file>` or  :option:`--vault-id <ansible-playbook --vault-id>`) is used. Alternately, you may specify the location of a password file or command Ansible to always prompt for the password in your ansible.cfg file. These options require no command line flag usage.

For best practices advice, refer to :ref:`best_practices_for_variables_and_vaults`.

.. _what_can_be_encrypted_with_vault:

What Can Be Encrypted With Vault
````````````````````````````````

File-level encryption
^^^^^^^^^^^^^^^^^^^^^

Ansible Vault can encrypt any structured data file used by Ansible.

This can include "group_vars/" or "host_vars/" inventory variables, variables loaded by "include_vars" or "vars_files", or variable files passed on the ansible-playbook command line with ``-e @file.yml`` or ``-e @file.json``.  Role variables and defaults are also included.

Ansible tasks, handlers, and so on are also data so these can be encrypted with vault as well. To hide the names of variables that you're using, you can encrypt the task files in their entirety.

Ansible Vault can also encrypt arbitrary files, even binary files.  If a vault-encrypted file is
given as the ``src`` argument to the :ref:`copy <copy_module>`, :ref:`template <template_module>`,
:ref:`unarchive <unarchive_module>`, :ref:`script <script_module>` or :ref:`assemble
<assemble_module>` modules, the file will be placed at the destination on the target host decrypted
(assuming a valid vault password is supplied when running the play).

.. note::
    The advantages of file-level encryption are that it is easy to use and that password rotation is straightforward with :ref:`rekeying <rekeying_files>`.
    The drawback is that the contents of files are no longer easy to access and read. This may be problematic if it is a list of tasks (when encrypting a variables file, :ref:`best practice <best_practices_for_variables_and_vaults>` is to keep references to these variables in a non-encrypted file).


Variable-level encryption
^^^^^^^^^^^^^^^^^^^^^^^^^

Ansible also supports encrypting single values inside a YAML file, using the `!vault` tag to let YAML and Ansible know it uses special processing. This feature is covered in more detail :ref:`below <encrypt_string_for_use_in_yaml>`.

.. note::
    The advantage of variable-level encryption is that files are still easily legible even if they mix plaintext and encrypted variables.
    The drawback is that password rotation is not as simple as with file-level encryption: the :ref:`rekey <ansible_vault_rekey>` command does not work with this method.


.. _vault_ids:

Vault IDs and Multiple Vault Passwords
``````````````````````````````````````


A vault ID is an identifier for one or more vault secrets;
Ansible supports multiple vault passwords.

Vault IDs provide labels to distinguish between individual vault passwords.

To use vault IDs, you must provide an ID *label* of your choosing and a *source* to obtain its password (either ``prompt`` or a file path):

.. code-block:: bash

   --vault-id label@source

This switch is available for all Ansible commands that can interact with vaults: :ref:`ansible-vault`, :ref:`ansible-playbook`, etc.

Vault-encrypted content can specify which vault ID it was encrypted with.

For example, a playbook can now include a vars file encrypted with a 'dev' vault
ID and a 'prod' vault ID.

.. note:
    Older versions of Ansible, before 2.4, only supported using one single vault password at a time.


.. _creating_files:

Creating Encrypted Files
````````````````````````

To create a new encrypted data file, run the following command:

.. code-block:: bash

   ansible-vault create foo.yml

First you will be prompted for a password. After providing a password, the tool will launch whatever editor you have defined with $EDITOR, and defaults to vi.  Once you are done with the editor session, the file will be saved as encrypted data.

The default cipher is AES (which is shared-secret based).

To create a new encrypted data file with the Vault ID 'password1' assigned to it and be prompted for the password, run:

.. code-block:: bash

   ansible-vault create --vault-id password1@prompt foo.yml


.. _editing_encrypted_files:

Editing Encrypted Files
```````````````````````

To edit an encrypted file in place, use the :ref:`ansible-vault edit <ansible_vault_edit>` command.
This command will decrypt the file to a temporary file and allow you to edit
the file, saving it back when done and removing the temporary file:

.. code-block:: bash

   ansible-vault edit foo.yml

To edit a file encrypted with the 'vault2' password file and assigned the 'pass2' vault ID:

.. code-block:: bash

   ansible-vault edit --vault-id pass2@vault2 foo.yml


.. _rekeying_files:

Rekeying Encrypted Files
````````````````````````

Should you wish to change your password on a vault-encrypted file or files, you can do so with the rekey command:

.. code-block:: bash

    ansible-vault rekey foo.yml bar.yml baz.yml

This command can rekey multiple data files at once and will ask for the original
password and also the new password.

To rekey files encrypted with the 'preprod2' vault ID and the 'ppold' file and be prompted for the new password:

.. code-block:: bash

    ansible-vault rekey --vault-id preprod2@ppold --new-vault-id preprod2@prompt foo.yml bar.yml baz.yml

A different ID could have been set for the rekeyed files by passing it to ``--new-vault-id``.

.. _encrypting_files:

Encrypting Unencrypted Files
````````````````````````````

If you have existing files that you wish to encrypt, use
the :ref:`ansible-vault encrypt <ansible_vault_encrypt>` command.  This command can operate on multiple files at once:

.. code-block:: bash

   ansible-vault encrypt foo.yml bar.yml baz.yml

To encrypt existing files with the 'project' ID and be prompted for the password:

.. code-block:: bash

   ansible-vault encrypt --vault-id project@prompt foo.yml bar.yml baz.yml

.. note::

   It is technically possible to separately encrypt files or strings with the *same* vault ID but *different* passwords, if different password files or prompted passwords are provided each time.
   This could be desirable if you use vault IDs as references to classes of passwords (rather than a single password) and you always know which specific password or file to use in context. However this may be an unnecessarily complex use-case.
   If two files are encrypted with the same vault ID but different passwords by accident, you can use the :ref:`rekey <rekeying_files>` command to fix the issue.


.. _decrypting_files:

Decrypting Encrypted Files
``````````````````````````

If you have existing files that you no longer want to keep encrypted, you can permanently decrypt
them by running the :ref:`ansible-vault decrypt <ansible_vault_decrypt>` command.  This command will save them unencrypted
to the disk, so be sure you do not want :ref:`ansible-vault edit <ansible_vault_edit>` instead:

.. code-block:: bash

    ansible-vault decrypt foo.yml bar.yml baz.yml


.. _viewing_files:

Viewing Encrypted Files
```````````````````````

If you want to view the contents of an encrypted file without editing it, you can use the :ref:`ansible-vault view <ansible_vault_view>` command:

.. code-block:: bash

    ansible-vault view foo.yml bar.yml baz.yml


.. _encrypt_string_for_use_in_yaml:

Use encrypt_string to create encrypted variables to embed in yaml
`````````````````````````````````````````````````````````````````

The :ref:`ansible-vault encrypt_string <ansible_vault_encrypt_string>` command will encrypt and format a provided string into a format
that can be included in :ref:`ansible-playbook` YAML files.

To encrypt a string provided as a cli arg:

.. code-block:: bash

    ansible-vault encrypt_string --vault-password-file a_password_file 'foobar' --name 'the_secret'

Result::

    the_secret: !vault |
          $ANSIBLE_VAULT;1.1;AES256
          62313365396662343061393464336163383764373764613633653634306231386433626436623361
          6134333665353966363534333632666535333761666131620a663537646436643839616531643561
          63396265333966386166373632626539326166353965363262633030333630313338646335303630
          3438626666666137650a353638643435666633633964366338633066623234616432373231333331
          6564

To use a vault-id label for 'dev' vault-id:

.. code-block:: bash

    ansible-vault encrypt_string --vault-id dev@a_password_file 'foooodev' --name 'the_dev_secret'

Result::

    the_dev_secret: !vault |
              $ANSIBLE_VAULT;1.2;AES256;dev
              30613233633461343837653833666333643061636561303338373661313838333565653635353162
              3263363434623733343538653462613064333634333464660a663633623939393439316636633863
              61636237636537333938306331383339353265363239643939666639386530626330633337633833
              6664656334373166630a363736393262666465663432613932613036303963343263623137386239
              6330

To encrypt a string read from stdin and name it 'db_password':

.. code-block:: bash

    echo -n 'letmein' | ansible-vault encrypt_string --vault-id dev@a_password_file --stdin-name 'db_password'

.. warning::

   This method leaves the string in your shell history. Do not use it outside of testing.

Result::

    Reading plaintext input from stdin. (ctrl-d to end input)
    db_password: !vault |
              $ANSIBLE_VAULT;1.2;AES256;dev
              61323931353866666336306139373937316366366138656131323863373866376666353364373761
              3539633234313836346435323766306164626134376564330a373530313635343535343133316133
              36643666306434616266376434363239346433643238336464643566386135356334303736353136
              6565633133366366360a326566323363363936613664616364623437336130623133343530333739
              3039

To be prompted for a string to encrypt, encrypt it, and give it the name 'new_user_password':


.. code-block:: bash

    ansible-vault encrypt_string --vault-id dev@a_password_file --stdin-name 'new_user_password'

Output::

    Reading plaintext input from stdin. (ctrl-d to end input)

User enters 'hunter2' and hits ctrl-d.

.. warning::

   Do not press Enter after supplying the string. That will add a newline to the encrypted value.

Result::

    new_user_password: !vault |
              $ANSIBLE_VAULT;1.2;AES256;dev
              37636561366636643464376336303466613062633537323632306566653533383833366462366662
              6565353063303065303831323539656138653863353230620a653638643639333133306331336365
              62373737623337616130386137373461306535383538373162316263386165376131623631323434
              3866363862363335620a376466656164383032633338306162326639643635663936623939666238
              3161

See also :ref:`single_encrypted_variable`

After you added the encrypted value to a var file (vars.yml), you can see the original value using the debug module.

.. code-block:: console

   ansible localhost -m debug -a var="new_user_password" -e "@vars.yml" --ask-vault-pass
   Vault password:

   localhost | SUCCESS => {
       "new_user_password": "hunter2"
   }


.. _providing_vault_passwords:

Providing Vault Passwords
`````````````````````````

When all data is encrypted using a single password the :option:`--ask-vault-pass <ansible-playbook --ask-vault-pass>`
or :option:`--vault-password-file <ansible-playbook --vault-password-file>` cli options should be used.

For example, to use a password store in the text file :file:`/path/to/my/vault-password-file`:

.. code-block:: bash

    ansible-playbook --vault-password-file /path/to/my/vault-password-file site.yml

To prompt for a password:

.. code-block:: bash

    ansible-playbook --ask-vault-pass site.yml

To get the password from a vault password executable script :file:`my-vault-password.py`:

.. code-block:: bash

    ansible-playbook --vault-password-file my-vault-password.py

The config option :ref:`DEFAULT_VAULT_PASSWORD_FILE` can be used to specify a vault password file so that the
:option:`--vault-password-file <ansible-playbook --vault-password-file>` cli option does not have to be
specified every time.


.. _specifying_vault_ids:

Labelling Vaults
^^^^^^^^^^^^^^^^

Since Ansible 2.4 the :option:`--vault-id <ansible-playbook --vault-id>` can be used to indicate which vault ID
('dev', 'prod', 'cloud', etc) a password is for as well as how to source the password (prompt, a file path, etc).

By default the vault-id label is only a hint, any values encrypted with the password will be decrypted.
The config option :ref:`DEFAULT_VAULT_ID_MATCH` can be set to require the vault id to match the vault ID
used when the value was encrypted.
This can reduce errors when different values are encrypted with different passwords.

For example, to use a password file :file:`dev-password` for the vault-id 'dev':

.. code-block:: bash

    ansible-playbook --vault-id dev@dev-password site.yml

To prompt for the password for the 'dev' vault ID:

.. code-block:: bash

    ansible-playbook --vault-id dev@prompt site.yml

To get the 'dev' vault ID password from an executable script :file:`my-vault-password.py`:

.. code-block:: bash

    ansible-playbook --vault-id dev@my-vault-password.py


The config option :ref:`DEFAULT_VAULT_IDENTITY_LIST` can be used to specify a default vault ID and password source
so that the :option:`--vault-id <ansible-playbook --vault-id>` cli option does not have to be specified every time.


The :option:`--vault-id <ansible-playbook --vault-id>` option can also be used without specifying a vault-id.
This behaviour is equivalent to :option:`--ask-vault-pass <ansible-playbook --ask-vault-pass>` or
:option:`--vault-password-file <ansible-playbook --vault-password-file>` so is rarely used.

For example, to use a password file :file:`dev-password`:

.. code-block:: bash

    ansible-playbook --vault-id dev-password site.yml

To prompt for the password:

.. code-block:: bash

    ansible-playbook --vault-id @prompt site.yml

To get the password from an executable script :file:`my-vault-password.py`:

.. code-block:: bash

    ansible-playbook --vault-id my-vault-password.py

.. note::
    Prior to Ansible 2.4, the :option:`--vault-id <ansible-playbook --vault-id>` option is not supported
    so :option:`--ask-vault-pass <ansible-playbook --ask-vault-pass>` or
    :option:`--vault-password-file <ansible-playbook --vault-password-file>` must be used.


Multiple Vault Passwords
^^^^^^^^^^^^^^^^^^^^^^^^

Ansible 2.4 and later support using multiple vault passwords, :option:`--vault-id <ansible-playbook --vault-id>` can
be provided multiple times.

For example, to use a 'dev' password read from a file and to be prompted for the 'prod' password:

.. code-block:: bash

    ansible-playbook --vault-id dev@dev-password --vault-id prod@prompt site.yml

By default the vault ID labels (dev, prod etc.) are only hints, Ansible will attempt to decrypt vault content
with each password. The password with the same label as the encrypted data will be tried first, after that
each vault secret will be tried in the order they were provided on the command line.

Where the encrypted data doesn't have a label, or the label doesn't match any of the provided labels, the
passwords will be tried in the order they are specified.

In the above case, the 'dev' password will be tried first, then the 'prod' password for cases
where Ansible doesn't know which vault ID is used to encrypt something.

To add a vault ID label to the encrypted data use the :option:`--vault-id <ansible-vault-create --vault-id>` option
with a label when encrypting the data.

The :ref:`DEFAULT_VAULT_ID_MATCH` config option can be set so that Ansible will only use the password with
the same label as the encrypted data. This is more efficient and may be more predictable when multiple
passwords are used.

The config option :ref:`DEFAULT_VAULT_IDENTITY_LIST` can have multiple values which is equivalent to multiple :option:`--vault-id <ansible-playbook --vault-id>` cli options.

The :option:`--vault-id <ansible-playbook --vault-id>` can be used in lieu of the :option:`--vault-password-file <ansible-playbook --vault-password-file>` or :option:`--ask-vault-pass <ansible-playbook --ask-vault-pass>` options,
or it can be used in combination with them.

When using :ref:`ansible-vault` commands that encrypt content (:ref:`ansible-vault encrypt <ansible_vault_encrypt>`, :ref:`ansible-vault encrypt_string <ansible_vault_encrypt_string>`, etc)
only one vault-id can be used.


.. _vault_password_client_scripts:

Vault Password Client Scripts
`````````````````````````````

When implementing a script to obtain a vault password it may be convenient to know which vault ID label was
requested. For example a script loading passwords from a secret manager may want to use the vault ID label to pick
either the 'dev' or 'prod' password.

Since Ansible 2.5 this is supported through the use of Client Scripts. A Client Script is an executable script
with a name ending in ``-client``. Client Scripts are used to obtain vault passwords in the same way as any other
executable script. For example:

.. code-block:: bash

    ansible-playbook --vault-id dev@contrib/vault/vault-keyring-client.py

The difference is in the implementation of the script. Client Scripts are executed with a ``--vault-id`` option
so they know which vault ID label was requested. So the above Ansible execution results in the below execution
of the Client Script:

.. code-block:: bash

    contrib/vault/vault-keyring-client.py --vault-id dev

:file:`contrib/vault/vault-keyring-client.py` is an example of Client Script that loads passwords from the
system keyring.


.. _speeding_up_vault:

Speeding Up Vault Operations
````````````````````````````

If you have many encrypted files, decrypting them at startup may cause a perceptible delay. To speed this up, install the cryptography package:

.. code-block:: bash

    pip install cryptography


.. _vault_format:

Vault Format
````````````

A vault encrypted file is a UTF-8 encoded txt file.

The file format includes a newline terminated header.

For example::

    $ANSIBLE_VAULT;1.1;AES256

or::

    $ANSIBLE_VAULT;1.2;AES256;vault-id-label

The header contains the vault format id, the vault format version, the vault cipher, and a vault-id label (with format version 1.2), separated by semi-colons ';'

The first field ``$ANSIBLE_VAULT`` is the format id. Currently ``$ANSIBLE_VAULT`` is the only valid file format id. This is used to identify files that are vault encrypted (via vault.is_encrypted_file()).

The second field (``1.X``) is the vault format version. All supported versions of ansible will currently default to '1.1' or '1.2' if a labeled vault-id is supplied. 

The '1.0' format is supported for reading only (and will be converted automatically to the '1.1' format on write). The format version is currently used as an exact string compare only (version numbers are not currently 'compared').

The third field (``AES256``) identifies the cipher algorithm used to encrypt the data. Currently, the only supported cipher is 'AES256'. [vault format 1.0 used 'AES', but current code always uses 'AES256']

The fourth field (``vault-id-label``) identifies the vault-id label used to encrypt the data. For example using a vault-id of ``dev@prompt`` results in a vault-id-label of 'dev' being used.

Note: In the future, the header could change. Anything after the vault id and version can be considered to depend on the vault format version. This includes the cipher id, and any additional fields that could be after that.

The rest of the content of the file is the 'vaulttext'. The vaulttext is a text armored version of the
encrypted ciphertext. Each line will be 80 characters wide, except for the last line which may be shorter.

Vault Payload Format 1.1 - 1.2
``````````````````````````````

The vaulttext is a concatenation of the ciphertext and a SHA256 digest with the result 'hexlifyied'.

'hexlify' refers to the ``hexlify()`` method of the Python Standard Library's `binascii <https://docs.python.org/3/library/binascii.html>`_ module.

hexlify()'ed result of:

- hexlify()'ed string of the salt, followed by a newline (``0x0a``)
- hexlify()'ed string of the crypted HMAC, followed by a newline. The HMAC is:

  - a `RFC2104 <https://www.ietf.org/rfc/rfc2104.txt>`_ style HMAC

    - inputs are:

      - The AES256 encrypted ciphertext
      - A PBKDF2 key. This key, the cipher key, and the cipher IV are generated from:

        - the salt, in bytes
        - 10000 iterations
        - SHA256() algorithm
        - the first 32 bytes are the cipher key
        - the second 32 bytes are the HMAC key
        - remaining 16 bytes are the cipher IV

-  hexlify()'ed string of the ciphertext. The ciphertext is:

  - AES256 encrypted data. The data is encrypted using:

    - AES-CTR stream cipher
    - cipher key
    - IV
    - a 128 bit counter block seeded from an integer IV
    - the plaintext

      - the original plaintext
      - padding up to the AES256 blocksize. (The data used for padding is based on `RFC5652 <https://tools.ietf.org/html/rfc5652#section-6.3>`_)


