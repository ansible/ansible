.. _vault:

*************
Ansible Vault
*************

Ansible Vault encrypts variables and files so you can keep sensitive data such as passwords or keys protected at rest, rather than as plaintext in playbooks or roles. To use Ansible Vault you need one or more passwords to encrypt and decrypt content. Once you have passwords, you can use the :ref:`ansible-vault` command-line tool to create and view encrypted variables, create encrypted files, encrypt existing files, or edit, re-key, or decrypt files. You can then distribute encrypted content or place it under source control and publish it more safely.

.. warning::
    * Vault ONLY protects data 'at rest'.  Once decrypted, play and plugin authors are responsible for avoiding any secret disclosure, see :ref:`no_log <keep_secret_data>` for details on hiding output.

Once you have encrypted variables and files, use them in ad-hoc commands and playbooks by passing one of the related command-line flags: :option:`--ask-vault-pass <ansible-playbook --ask-vault-pass>`, :option:`--vault-password-file <ansible-playbook --vault-password-file>` or  :option:`--vault-id <ansible-playbook --vault-id>`, with the encryption password, file, or ID. If you prefer, you can modify your ``ansible.cfg`` file to specify the location of a password file or configure Ansible to always prompt for the password. These options require no command line flag usage. You can also use a script to access encryption passwords stored in a third-party tool such as a secret manager.

.. contents::
   :local:

.. _vault_ids:

Managing vault passwords
========================

This section helps you develop a strategy for managing vault passwords, so you can track and use your encrypted content with confidence. Each time you encrypt a variable or file with Ansible Vault, you must provide a password. When you use the encrypted variable or file in a command or playbook, you must provide the password that was used to encrypt it. You can encrypt all your content with the same password, or use different passwords for different needs. If you use multiple passwords, you can use vault IDs to differentiate and manage them.

Single password or multiple passwords?
--------------------------------------

If you have a small team and few sensitive values, you might be able to use a single password for everything you encrypt with Ansible Vault. Using a single password for all encrypted content was the only option with older versions of Ansible, before 2.4.

Most users want multiple vault passwords. For example, it is common to use different passwords for different users or different levels of access. Depending on your needs, you might want a different password for each encrypted file, for each directory, or for each environment. For example, you might have a playbook that includes two vars files, one for the dev environment and one for the production environment, encrypted with two different passwords. When you run the playbook, select the correct vault password for the environment you are targeting.

Managing multiple passwords with vault IDs
------------------------------------------

If you use multiple vault passwords, you can differentiate one password from another with the :option:`--vault-id <ansible-playbook --vault-id>` option. The :option:`--vault-id <ansible-playbook --vault-id>` option works with any Ansible command that interacts with vaults, including :ref:`ansible-vault`, :ref:`ansible-playbook`, and so on. The pattern looks like this:

.. code-block:: bash

   --vault-id label@source

When you create encrypted variables or files, :option:`--vault-id <ansible-playbook --vault-id>` option adds a label (a hint or nickname) to encrypted content, to help you remember which password you used to encrypt it. When you encrypt a variable or file with a vault ID, the encrypted variable or file displays the vault ID label in plain text in the header. The vault ID is the last element before the encrypted content. If you use vault IDs and store your passwords in a file or a secret manager, include the matching label when you store the password.

When running tasks and playbooks, you can use :option:`--vault-id <ansible-playbook --vault-id>` option by itself, with :option:`--vault-password-file <ansible-playbook --vault-password-file>`, or with :option:`--ask-vault-pass <ansible-playbook --ask-vault-pass>`. When you use encrypted files with ``--vault-id``, you must pass a label (a hint or nickname) and a source (a prompt or file) for the matching password.  See below for examples of encrypting content with vault IDs and using content encrypted with vault IDs.

Limitations of vault IDs
^^^^^^^^^^^^^^^^^^^^^^^^

Ansible does not enforce using the same password every time you use a particular vault ID. You can encrypt different variables or files with the same vault ID but different passwords. This usually happens when you type the password at a prompt and make a mistake. It is possible to use different passwords with the same vault ID on purpose. For example, you could use each vault ID as a reference to a class of passwords, rather than a single password. In this scenario, you must always know which specific password or file to use in context. However, you are more likely to encrypt two files with the same vault ID and different passwords by accident. If you encrypt two files with the same vault ID but different passwords by accident, you can use the :ref:`rekey <rekeying_files>` command to fix the issue.

Enforcing vault ID matching
^^^^^^^^^^^^^^^^^^^^^^^^^^^

By default the vault ID label is only a hint to help you remember which password you used to encrypt a variable or file. Ansible does not check that the vault ID in the header of the encrypted content matches the vault ID you provide when you use the content. Ansible decrypts all files and variables called by your command or playbook that are encrypted with the password you provide. To decrypt only content with the vault ID you provide, set the config option :ref:`DEFAULT_VAULT_ID_MATCH`. When you set :ref:`DEFAULT_VAULT_ID_MATCH`, each password is only used to decrypt data that was encrypted with the same label. This is efficient, predictable, and can reduce errors when different values are encrypted with different passwords. Even with the :ref:`DEFAULT_VAULT_ID_MATCH` setting enabled, Ansible does not enforce using the same password every time you use a particular vault ID.

Storing and accessing vault passwords
-------------------------------------

Although you can try to memorize passwords, most users store them securely and access them as needed. You have two main options for storing passwords: in files, or in a third-party tool like the system keyring or a secret manager. If you store your passwords in a third-party tool, you need a vault password client script to retrieve them.

Storing passwords in files
^^^^^^^^^^^^^^^^^^^^^^^^^^

To store a vault password in a file, enter the password as a string on a single line in the file. You can create a separate file for each password, or start each line with the vault ID to differentiate among multiple passwords in a single file. Make sure the permissions on your password file(s) are appropriate. Do not add the file(s) to source control.

.. _vault_password_client_scripts:

Using third-party tools with vault password client scripts
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

You can store your vault passwords on the system keyring, in a database, or in a secret manager. Include your vault IDs when you store these passwords. To retrieve passwords stored this way, create a vault password client script. To write a vault password client script:

  * Give the script a name ending in ``-client``
  * Make the script executable
  * Print the password(s) to standard output
  * If the script needs to prompt for data (for example, a database password), send the prompts to standard error

The user specifies the script with the ``--vault-id`` flag. For example:

.. code-block:: bash

    ansible-playbook --vault-id dev@contrib/vault/vault-keyring-client.py

Ansible executes the client script with a ``--vault-id`` option so the script knows which vault ID label the user requested. For example a script loading passwords from a secret manager can use the vault ID label to pick either the 'dev' or 'prod' password. The example command above results in the following execution of the client script:

.. code-block:: bash

    contrib/vault/vault-keyring-client.py --vault-id dev

:file:`contrib/vault/vault-keyring-client.py` is an example of Client Script that loads passwords from the
system keyring.


Encrypting content with vault
=============================

Once you have a strategy for creating, storing, and using vault passwords, you can start encrypting content. You can encrypt two types of content with Ansible Vault: variables and files. Encrypted variables and files always include the ``!vault`` tag, which tells Ansible and YAML that the content needs to be decrypted, and a ``|`` character, which allows multi-line strings. For more details about the encryption process and the format of content encrypted with Ansible Vault, see :ref:`vault_format`. This table shows the main differences between encrypted variables and encrypted files:

.. table::
   :class: documentation-table

   ====================== =========================================== ====================================
   ..                     Encrypted variables                         Encrypted files
   ====================== =========================================== ====================================
   Encrypted              Variables within a plaintext file           The entire file

   Decrypted              On demand, only when needed                 Whenever loaded or referenced [#f1]_

   Allowed content        Only variables, not tasks or other content  Any structured data file

   ====================== =========================================== ====================================

.. [#f1] Ansible cannot know if it needs content from an encrypted file unless it decrypts the file, so it decrypts all encrypted files referenced in your playbooks and roles.

.. _encrypting_variables:
.. _single_encrypted_variable:

Encrypting individual variables with vault
------------------------------------------

You can encrypt single values inside a YAML file using the :ref:`ansible-vault encrypt_string <ansible_vault_encrypt_string>` command. This command encrypts the value and adds the ``!vault`` tag, which lets YAML and Ansible know the tagged variable uses special processing. For one way to keep your vaulted variables safely visible, see :ref:`tip_for_variables_and_vaults`.

Advantages and disadvantages of encrypting variables
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The advantage of variable-level encryption is that files are still easily legible. You can mix plaintext and encrypted variables, even inline in a play or role. The disadvantage is that password rotation is not as simple as with file-level encryption: the :ref:`rekey <ansible_vault_rekey>` command does not work with encrypted variables. Also, if you want to encrypt tasks or other content beyond variables, you must encrypt the entire file.

.. _encrypt_string_for_use_in_yaml:

Creating encrypted variables
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The :ref:`ansible-vault encrypt_string <ansible_vault_encrypt_string>` command encrypts and formats any string you type (or copy or generate) into a format that can be included in a playbook, role, or variables file. The pattern looks like this:

.. code-block:: bash

    ansible-vault encrypt_string <password_source> '<content_of_variable>' --name '<name_of_variable>'

For example, to encrypt a string using a password stored in a file, provided as a cli arg:

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

Add the results from any of the examples above to any playbook, variables file, or role for future use.

Viewing encrypted variables
^^^^^^^^^^^^^^^^^^^^^^^^^^^

You can view the original value of an encrypted variable using the debug module. You must pass the correct password to decrypt the variable.

.. code-block:: console

   ansible localhost -m debug -a var="new_user_password" -e "@vars.yml" --ask-vault-pass
   Vault password:

   localhost | SUCCESS => {
       "new_user_password": "hunter2"
   }


Encrypting files with vault
---------------------------

Ansible vault can encrypt any structured data file used by Ansible, including:

  * group variables files from inventory
  * host variables files from inventory
  * variables files passed to ansible-playbook with ``-e @file.yml`` or ``-e @file.json``
  * variables files loaded by ``include_vars`` or ``vars_files``
  * variables files in roles
  * defaults files in roles
  * tasks files
  * handlers files
  * binary files or other arbitrary files

The full file is encrypted in the vault.

Advantages and disadvantages of encrypting files
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

File-level encryption is easy to use. Password rotation for encrypted files is straightforward with the :ref:`rekey <rekeying_files>` command. Encrypting files can hide not only sensitive values, but the names of the variables you use.

The disadvantage of file-level encryption is that the contents of files are no longer easy to access and read. This may be a problem for encrypted tasks files. When encrypting a variables file, see :ref:`tip_for_variables_and_vaults` for one way to keep references to these variables in a non-encrypted file. Ansible always decrypts the entire encrypted file when it is when loaded or referenced, because Ansible cannot know if it needs the content unless it decrypts it.

.. _creating_files:

Creating encrypted files
^^^^^^^^^^^^^^^^^^^^^^^^

To create a new encrypted data file:

.. code-block:: bash

   ansible-vault create foo.yml

At the prompt, provide a password. Save the password for future use. The tool launches an editor (whatever editor you have defined with $EDITOR, default editor is vi). Add the content. When you close the the editor session, the file is saved as encrypted data.

To create a new encrypted data file with the Vault ID 'password1' assigned to it and be prompted for the password, run:

.. code-block:: bash

   ansible-vault create --vault-id password1@prompt foo.yml


.. _encrypting_files:

Encrypting existing files
^^^^^^^^^^^^^^^^^^^^^^^^^

To encrypt an existing file, use the :ref:`ansible-vault encrypt <ansible_vault_encrypt>` command. This command can operate on multiple files at once. For example:

.. code-block:: bash

   ansible-vault encrypt foo.yml bar.yml baz.yml

To encrypt existing files with the 'project' ID and be prompted for the password:

.. code-block:: bash

   ansible-vault encrypt --vault-id project@prompt foo.yml bar.yml baz.yml


.. _viewing_files:

Viewing encrypted files
^^^^^^^^^^^^^^^^^^^^^^^

To view the contents of an encrypted file without editing it, you can use the :ref:`ansible-vault view <ansible_vault_view>` command:

.. code-block:: bash

    ansible-vault view foo.yml bar.yml baz.yml


.. _editing_encrypted_files:

Editing encrypted files
^^^^^^^^^^^^^^^^^^^^^^^

To edit an encrypted file in place, use the :ref:`ansible-vault edit <ansible_vault_edit>` command. This command decrypts the file to a temporary file, allows you to edit the content, then saves and re-encrypts the content and removes the temporary file when you close the editor. For example:

.. code-block:: bash

   ansible-vault edit foo.yml

To edit a file encrypted with the 'vault2' password file and assigned the 'pass2' vault ID:

.. code-block:: bash

   ansible-vault edit --vault-id pass2@vault2 foo.yml


.. _rekeying_files:

Changing the password and/or vault ID on encrypted files
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To change the password on a vault-encrypted file or files, use the rekey command:

.. code-block:: bash

    ansible-vault rekey foo.yml bar.yml baz.yml

This command can rekey multiple data files at once and will ask for the original password and also the new password. To set a different ID for the rekeyed files, pass the new ID to ``--new-vault-id``. For example, to rekey a list of files encrypted with the 'preprod2' vault ID and the 'ppold' file and be prompted for the new password:

.. code-block:: bash

    ansible-vault rekey --vault-id preprod2@ppold --new-vault-id preprod2@prompt foo.yml bar.yml baz.yml


.. _decrypting_files:

Decrypting encrypted files
^^^^^^^^^^^^^^^^^^^^^^^^^^

If you have an encrypted file that you no longer want to keep encrypted, you can permanently decrypt it by running the :ref:`ansible-vault decrypt <ansible_vault_decrypt>` command. This command will save the file unencrypted to the disk, so be sure you do not want to :ref:`edit <ansible_vault_edit>` it instead.

.. code-block:: bash

    ansible-vault decrypt foo.yml bar.yml baz.yml


.. _playbooks_vault:
.. _providing_vault_passwords:

Using vaulted variables and files
=================================

When you run a task or playbook that uses encrypted variables or files, you must provide the credentials to decrypt the variables or files. You can do this at the command line or in the playbook itself.

Passing a single password
-------------------------

If all the encrypted variables and files your task or playbook needs use a single password, you can use the :option:`--ask-vault-pass <ansible-playbook --ask-vault-pass>` or :option:`--vault-password-file <ansible-playbook --vault-password-file>` cli options.

To prompt for the password:

.. code-block:: bash

    ansible-playbook --ask-vault-pass site.yml

To retrieve the password from the :file:`/path/to/my/vault-password-file` file:

.. code-block:: bash

    ansible-playbook --vault-password-file /path/to/my/vault-password-file site.yml

To get the password from the vault password client script :file:`my-vault-password.py`:

.. code-block:: bash

    ansible-playbook --vault-password-file my-vault-password.py


.. _specifying_vault_ids:

Passing vault IDs
-----------------

You can also use the :option:`--vault-id <ansible-playbook --vault-id>` option to pass a single password with its vault label. This approach is clearer when multiple vaults are used within a single inventory.

To prompt for the password for the 'dev' vault ID:

.. code-block:: bash

    ansible-playbook --vault-id dev@prompt site.yml

To retrieve the password for the 'dev' vault ID from the :file:`dev-password` file:

.. code-block:: bash

    ansible-playbook --vault-id dev@dev-password site.yml

To get the password for the 'dev' vault ID from the vault password client script :file:`my-vault-password.py`:

.. code-block:: bash

    ansible-playbook --vault-id dev@my-vault-password.py

Using `--vault-id` without a vault ID
-------------------------------------

The :option:`--vault-id <ansible-playbook --vault-id>` option can also be used without specifying a vault-id. This behavior is equivalent to :option:`--ask-vault-pass <ansible-playbook --ask-vault-pass>` or :option:`--vault-password-file <ansible-playbook --vault-password-file>` so is rarely used.

For example, to use a password file :file:`dev-password`:

.. code-block:: bash

    ansible-playbook --vault-id dev-password site.yml

To prompt for the password:

.. code-block:: bash

    ansible-playbook --vault-id @prompt site.yml

To get the password from an executable script :file:`my-vault-password.py`:

.. code-block:: bash

    ansible-playbook --vault-id my-vault-password.py


Passing multiple vault passwords
--------------------------------

If your task or playbook requires multiple encrypted variables or files that you encrypted with different vault IDs, you must use the :option:`--vault-id <ansible-playbook --vault-id>` option, passing multiple ``--vault-id`` options to specify the vault IDs ('dev', 'prod', 'cloud', 'db') and sources for the passwords (prompt, file, script). . For example, to use a 'dev' password read from a file and to be prompted for the 'prod' password:

.. code-block:: bash

    ansible-playbook --vault-id dev@dev-password --vault-id prod@prompt site.yml

By default the vault ID labels (dev, prod etc.) are only hints. Ansible attempts to decrypt vault content with each password. The password with the same label as the encrypted data will be tried first, after that each vault secret will be tried in the order they were provided on the command line.

Where the encrypted data has no label, or the label does not match any of the provided labels, the passwords will be tried in the order they are specified. In the example above, the 'dev' password will be tried first, then the 'prod' password for cases where Ansible doesn't know which vault ID is used to encrypt something.

Configuring defaults for using encrypted content
================================================

Setting a default vault ID
--------------------------

If you use one vault ID more than any other, you can set the config option :ref:`DEFAULT_VAULT_IDENTITY_LIST` to specify a default vault ID and password source. Ansible will use the default vault ID and source any time you do not specify :option:`--vault-id <ansible-playbook --vault-id>`. You can set multiple values for this option. Setting multiple values is equivalent to passing multiple :option:`--vault-id <ansible-playbook --vault-id>` cli options.

Setting a default password source
---------------------------------

If you use one vault password file more than any other, you can set the :ref:`DEFAULT_VAULT_PASSWORD_FILE` config option or the :envvar:`ANSIBLE_VAULT_PASSWORD_FILE` environment variable to specify that file. For example, if you set ``ANSIBLE_VAULT_PASSWORD_FILE=~/.vault_pass.txt``, Ansible will automatically search for the password in that file. This is useful if, for example, you use Ansible from a continuous integration system like Jenkins.

When encrypted files are visible
================================

In general, Ansible does not display the contents of encrypted files during execution. Content you encrypt with Ansible vault remains encrypted. However, there is one exception. If you pass a vault-encrypted file as the ``src`` argument to the :ref:`copy <copy_module>`, :ref:`template <template_module>`, :ref:`unarchive <unarchive_module>`, :ref:`script <script_module>` or :ref:`assemble <assemble_module>` module, the file will not be encrypted on the target host (assuming you supply the correct vault password when you run the play). This behavior is intended and useful. You can encrypt a configuration file or template to avoid sharing the details of your configuration, but when you copy that configuration to servers in your environment, you want it to be decrypted so local users and processes can access it.

.. _speeding_up_vault:

Speeding up vault operations
============================

If you have many encrypted files, decrypting them at startup may cause a perceptible delay. To speed this up, install the cryptography package:

.. code-block:: bash

    pip install cryptography


.. _vault_format:

Format of vault-encrypted content
=================================

A vault encrypted file is a UTF-8 encoded txt file. The file format includes a newline terminated header. For example::

    $ANSIBLE_VAULT;1.1;AES256

or::

    $ANSIBLE_VAULT;1.2;AES256;vault-id-label

The header contains up to four elements, separated by semi-colons (``;``).

  1. The format ID (``$ANSIBLE_VAULT``). Currently ``$ANSIBLE_VAULT`` is the only valid format ID. The format ID identifies content that is encrypted with Ansible vault (via vault.is_encrypted_file()).

  2. The vault format version (``1.X``). All supported versions of Ansible will currently default to '1.1' or '1.2' if a labeled vault ID is supplied. The '1.0' format is supported for reading only (and will be converted automatically to the '1.1' format on write). The format version is currently used as an exact string compare only (version numbers are not currently 'compared').

  3. The cipher algorithm used to encrypt the data (``AES256``). Currently ``AES256`` is the only supported cipher algorithm. Vault format 1.0 used 'AES', but current code always uses 'AES256'.

  4. The vauld ID label used to encrypt the data (optional, ``vault-id-label``) For example, if you encrypt a file with ``--vault-id dev@prompt``, the vault-id-label is ``dev``.

Note: In the future, the header could change. Fields after the format ID and format version depend on the format version, and future vault format versions may add more cipher algorithm options and/or additional fields.

The rest of the content of the file is the 'vaulttext'. The vaulttext is a text armored version of the
encrypted ciphertext. Each line is 80 characters wide, except for the last line which may be shorter.

Vault payload format 1.1 - 1.2
------------------------------

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
