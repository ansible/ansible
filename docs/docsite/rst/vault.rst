Ansible Vault
=============

.. contents:: Topics

Ansible Vault is a feature of ansible that allows you to keep sensitive data such as passwords or keys in encrypted files, rather than as plaintext in playbooks or roles. These vault files can then be distributed or placed in source control.

To enable this feature, a command line tool - :ref:`ansible-vault` - is used to edit files, and a command line flag (:option:`--ask-vault-pass <ansible-playbook --ask-vault-pass>` or :option:`--vault-password-file <ansible-playbook --vault-password-file>`) is used. Alternately, you may specify the location of a password file or command Ansible to always prompt for the password in your ansible.cfg file. These options require no command line flag usage.

For best practices advice, refer to :ref:`best_practices_for_variables_and_vaults`.

.. _what_can_be_encrypted_with_vault:

What Can Be Encrypted With Vault
````````````````````````````````

Ansible Vault can encrypt any structured data file used by Ansible.  This can include "group_vars/" or "host_vars/" inventory variables, variables loaded by "include_vars" or "vars_files", or variable files passed on the ansible-playbook command line with ``-e @file.yml`` or ``-e @file.json``.  Role variables and defaults are also included.

Ansible tasks, handlers, and so on are also data so these can be encrypted with vault as well. To hide the names of variables that you're using, you can encrypt the task files in their entirety.

Ansible Vault can also encrypt arbitrary files, even binary files.  If a vault-encrypted file is
given as the ``src`` argument to the :ref:`copy <copy>`, :ref:`template <template>`,
:ref:`unarchive <unarchive>`, :ref:`script <script>` or :ref:`assemble <assemble>` modules, the file will be placed at the destination on the target host decrypted (assuming a valid vault password is supplied when running the play).

As of version 2.3, Ansible supports encrypting single values inside a YAML file, using the `!vault` tag to let YAML and Ansible know it uses special processing. This feature is covered in more details below.


.. _creating_files:

Creating Encrypted Files
````````````````````````

To create a new encrypted data file, run the following command:

.. code-block:: bash

   ansible-vault create foo.yml

First you will be prompted for a password.  The password used with vault currently must be the same for all files you wish to use together at the same time.

After providing a password, the tool will launch whatever editor you have defined with $EDITOR, and defaults to vi (before 2.1 the default was vim).  Once you are done with the editor session, the file will be saved as encrypted data.

The default cipher is AES (which is shared-secret based).


.. _editing_encrypted_files:

Editing Encrypted Files
```````````````````````

To edit an encrypted file in place, use the :ref:`ansible-vault edit <ansible_vault_edit>` command.
This command will decrypt the file to a temporary file and allow you to edit
the file, saving it back when done and removing the temporary file:

.. code-block:: bash

   ansible-vault edit foo.yml


.. _rekeying_files:

Rekeying Encrypted Files
````````````````````````

Should you wish to change your password on a vault-encrypted file or files, you can do so with the rekey command:

.. code-block:: bash

    ansible-vault rekey foo.yml bar.yml baz.yml

This command can rekey multiple data files at once and will ask for the original
password and also the new password.


.. _encrypting_files:

Encrypting Unencrypted Files
````````````````````````````

If you have existing files that you wish to encrypt, use
the :ref:`ansible-vault encrypt <ansible_vault_encrypt>` command.  This command can operate on multiple files at once:

.. code-block:: bash

   ansible-vault encrypt foo.yml bar.yml baz.yml


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

    ansible-vault encrypt_string --vault-id a_password_file 'foobar' --name 'the_secret'

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

    ansible-vault encrypt_string --vault-id dev@password 'foooodev' --name 'the_dev_secret'

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

    echo 'letmein' | ansible-vault encrypt_string --vault-id dev@password --stdin-name 'db_password'

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

    ansible-vault encrypt_string --vault-id dev@./password --stdin-name 'new_user_password'

Output::

    Reading plaintext input from stdin. (ctrl-d to end input)

User enters 'hunter42' and hits ctrl-d.

Result::

    new_user_password: !vault |
              $ANSIBLE_VAULT;1.2;AES256;dev
              37636561366636643464376336303466613062633537323632306566653533383833366462366662
              6565353063303065303831323539656138653863353230620a653638643639333133306331336365
              62373737623337616130386137373461306535383538373162316263386165376131623631323434
              3866363862363335620a376466656164383032633338306162326639643635663936623939666238
              3161

See also :ref:`single_encrypted_variable`


.. _vault_ids:

Vault Ids and Multiple Vault Passwords
``````````````````````````````````````

*Available since Ansible 2.4*

A vault id is an identifier for one or more vault secrets. Since Ansible 2.4,
Ansible supports multiple vault passwords. Vault ids is a way to provide
a label for a particular vault password.

Vault encrypted content can specify which vault id it was encrypted with.

Prior to Ansible 2.4, only one vault password could be used at a time. Post
Ansible 2.4, multiple vault passwords can be used each time Ansible runs, so any
vault files or vars that needed to be decrypted all had to use the same password.

Since Ansible 2.4, vault files or vars can be that are encrypted with different
passwords can be used at the same time.

For example, a playbook can now include a vars file encrypted with a 'dev' vault
id and a 'prod' vault id.

.. _providing_vault_passwords:

Providing Vault Passwords
`````````````````````````

Since Ansible 2.4, the recommended way to provide a vault password from the cli is
to use the :option:`--vault-id <ansible-playbook --vault-id>` cli option.

For example, to use a password store in the text file :file:`/path/to/my/vault-password-file`:

.. code-block:: bash

    ansible-playbook --vault-id /path/to/my/vault-password-file site.yml

To prompt for a password:

.. code-block:: bash

    ansible-playbook --vault-id @prompt site.yml

To get the password from a vault password executable script :file:`my-vault-password.py`:

.. code-block:: bash

    ansible-playbook --vault-id my-vault-password.py

The value for :option:`--vault-id <ansible-playbook --vault-id>` can specify the type of vault id (prompt, a file path, etc)
and a label for the vault id ('dev', 'prod', 'cloud', etc)

For example, to use a password file :file:`dev-password` for the vault-id 'dev':

.. code-block:: bash

    ansible-playbook --vault-id dev@dev-password site.yml

To prompt for the 'dev' vault id:

.. code-block:: bash

    ansible-playbook --vault-id dev@prompt site.yml

*Prior to Ansible 2.4*

To be prompted for a vault password, use the :option:`--ask-vault-pass <ansible-playbook --vault-id>` cli option:

.. code-block:: bash

    ansible-playbook --ask-vault-pass site.yml

To specify a vault password in a text file 'dev-password', use the :option:`--vault-password-file <ansible-playbook --vault-password-file>` option:

.. code-block:: bash

    ansible-playbook --vault-password-file dev-password site.yml

There is a config option (:ref:`DEFAULT_VAULT_PASSWORD_FILE`) to specify a vault password file to use
without requiring the :option:`--vault-password-file <ansible-playbook --vault-password-file>` cli option.


Multiple vault passwords
^^^^^^^^^^^^^^^^^^^^^^^^

Since Ansible 2.4 and later support using multiple vault passwords, :option:`--vault-id <ansible-playbook --vault-id>` can
be provided multiple times.

If multiple vault passwords are provided, by default Ansible will attempt to decrypt vault content
by trying each vault secret in the order they were provided on the command line.

For example, to use a 'dev' password read from a file and to be prompted for the 'prod' password:

.. code-block:: bash

    ansible-playbook --vault-id dev@dev-password --vault-id prod@prompt site.yml

In the above case, the 'dev' password will be tried first, then the 'prod' password for cases
where Ansible doesn't know which vault id is used to encrypt something.

If the vault content was encrypted using a :option:`--vault-id <ansible-vault --vault-id>` option, then the label of the
vault id is stored with the vault content. When Ansible knows the right vault-id, it will try
the matching vault id's secret first before trying the rest of the vault-ids.

There is a config option (:ref:`DEFAULT_VAULT_ID_MATCH` ) to force the vault content's vault id label to match with one of
the provided vault ids. But the default is to try the matching id first, then try the other
vault ids in order.

There is also a config option (:ref:`DEFAULT_VAULT_IDENTITY_LIST`) to specify a default list of vault ids to
use. For example, instead of requiring the cli option on every use, the (:ref:`DEFAULT_VAULT_IDENTITY_LIST`) config option can be used:

.. code-block:: bash

    ansible-playbook --vault-id dev@dev-password --vault-id prod@prompt site.yml

The :option:`--vault-id <ansible-playbook --vault-id>` can be used in lieu of the :option:`--vault-password-file <ansible-playbook --vault-password-file>` or :option:`--ask-vault-pass <ansible-playbook --ask-vault-pass>` options,
or it can be used in combination with them.

When using :ref:`ansible-vault` commands that encrypt content (:ref:`ansible-vault encrypt <ansible_vault_encrypt>`, :ref:`ansible-vault encrypt_string <ansible_vault_encrypt_string>`, etc)
only one vault-id can be used.



.. note::
    Prior to Ansible 2.4, only one vault password could be used in each Ansible run. The
    :option:`--vault-id <ansible-playbook --vault-id>` option is not support prior to Ansible 2.4.


.. _speeding_up_vault:

Speeding Up Vault Operations
````````````````````````````

By default, Ansible uses PyCrypto to encrypt and decrypt vault files. If you have many encrypted files, decrypting them at startup may cause a perceptible delay. To speed this up, install the cryptography package:

.. code-block:: bash

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

  - a `RFC2104 <https://www.ietf.org/rfc/rfc2104.txt>`_ style HMAC

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
        - padding up to the AES256 blocksize. (The data used for padding is based on `RFC5652 <https://tools.ietf.org/html/rfc5652#section-6.3>`_)


