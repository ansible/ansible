.. _vault_encrypting_content:

Encrypting content with Ansible Vault
=====================================

Once you have a strategy for managing and storing vault passwords, you can start encrypting content. You can encrypt two types of content with Ansible Vault: variables and files. Encrypted content always includes the ``!vault`` tag, which tells Ansible and YAML that the content needs to be decrypted, and a ``|`` character, which allows multi-line strings. Encrypted content created with ``--vault-id`` also contains the vault ID label. For more details about the encryption process and the format of content encrypted with Ansible Vault, see :ref:`vault_format`. This table shows the main differences between encrypted variables and encrypted files:

.. table::
   :class: documentation-table

   ====================== ================================= ====================================
   ..                     Encrypted variables                         Encrypted files
   ====================== ================================= ====================================
   How much is encrypted? Variables within a plaintext file The entire file

   When is it decrypted?  On demand, only when needed       Whenever loaded or referenced [#f1]_

   What can be encrypted? Only variables                    Any structured data file

   ====================== ================================= ====================================

.. [#f1] Ansible cannot know if it needs content from an encrypted file unless it decrypts the file, so it decrypts all encrypted files referenced in your playbooks and roles.

.. _encrypting_variables:
.. _single_encrypted_variable:

Encrypting individual variables with Ansible Vault
--------------------------------------------------

You can encrypt single values inside a YAML file using the :ref:`ansible-vault encrypt_string <ansible_vault_encrypt_string>` command. For one way to keep your vaulted variables safely visible, see :ref:`tip_for_variables_and_vaults`.

Advantages and disadvantages of encrypting variables
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

With variable-level encryption, your files are still easily legible. You can mix plaintext and encrypted variables, even inline in a play or role. However, password rotation is not as simple as with file-level encryption. You cannot :ref:`rekey <rekeying_files>` encrypted variables. Also, variable-level encryption only works on variables. If you want to encrypt tasks or other content, you must encrypt the entire file.

.. _encrypt_string_for_use_in_yaml:

Creating encrypted variables
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The :ref:`ansible-vault encrypt_string <ansible_vault_encrypt_string>` command encrypts and formats any string you type (or copy or generate) into a format that can be included in a playbook, role, or variables file. To create a basic encrypted variable, pass three options to the :ref:`ansible-vault encrypt_string <ansible_vault_encrypt_string>` command:

  * a source for the vault password (prompt, file, or script, with or without a vault ID)
  * the string to encrypt
  * the string name (the name of the variable)

The pattern looks like this:

.. code-block:: bash

    ansible-vault encrypt_string <password_source> '<string_to_encrypt>' --name '<string_name_of_variable>'

For example, to encrypt the string 'foobar' using the only password stored in 'a_password_file' and name the variable 'the_secret':

.. code-block:: bash

    ansible-vault encrypt_string --vault-password-file a_password_file 'foobar' --name 'the_secret'

The command above creates this content:

 .. code-block:: yaml

    the_secret: !vault |
          $ANSIBLE_VAULT;1.1;AES256
          62313365396662343061393464336163383764373764613633653634306231386433626436623361
          6134333665353966363534333632666535333761666131620a663537646436643839616531643561
          63396265333966386166373632626539326166353965363262633030333630313338646335303630
          3438626666666137650a353638643435666633633964366338633066623234616432373231333331
          6564

To encrypt the string 'foooodev', add the vault ID label 'dev' with the 'dev' vault password stored in 'a_password_file', and call the encrypted variable 'the_dev_secret':

.. code-block:: bash

    ansible-vault encrypt_string --vault-id dev@a_password_file 'foooodev' --name 'the_dev_secret'

The command above creates this content:

 .. code-block:: yaml

    the_dev_secret: !vault |
              $ANSIBLE_VAULT;1.2;AES256;dev
              30613233633461343837653833666333643061636561303338373661313838333565653635353162
              3263363434623733343538653462613064333634333464660a663633623939393439316636633863
              61636237636537333938306331383339353265363239643939666639386530626330633337633833
              6664656334373166630a363736393262666465663432613932613036303963343263623137386239
              6330

To encrypt the string 'letmein' read from stdin, add the vault ID 'dev' using the 'dev' vault password stored in `a_password_file`, and name the variable 'db_password':

.. code-block:: bash

    echo -n 'letmein' | ansible-vault encrypt_string --vault-id dev@a_password_file --stdin-name 'db_password'

.. warning::

   Typing secret content directly at the command line (without a prompt) leaves the secret string in your shell history. Do not do this outside of testing.

The command above creates this output:

 .. code-block:: console

    Reading plaintext input from stdin. (ctrl-d to end input, twice if your content does not already have a new line)
    db_password: !vault |
              $ANSIBLE_VAULT;1.2;AES256;dev
              61323931353866666336306139373937316366366138656131323863373866376666353364373761
              3539633234313836346435323766306164626134376564330a373530313635343535343133316133
              36643666306434616266376434363239346433643238336464643566386135356334303736353136
              6565633133366366360a326566323363363936613664616364623437336130623133343530333739
              3039

To be prompted for a string to encrypt, encrypt it with the 'dev' vault password from 'a_password_file', name the variable 'new_user_password' and give it the vault ID label 'dev':

.. code-block:: bash

    ansible-vault encrypt_string --vault-id dev@a_password_file --stdin-name 'new_user_password'

The command above triggers this prompt:

.. code-block:: text

    Reading plaintext input from stdin. (ctrl-d to end input, twice if your content does not already have a new line)

Type the string to encrypt (for example, 'hunter2'), hit ctrl-d, and wait.

.. warning::

   Do not press ``Enter`` after supplying the string to encrypt. That will add a newline to the encrypted value.

The sequence above creates this output:

 .. code-block:: yaml

    new_user_password: !vault |
              $ANSIBLE_VAULT;1.2;AES256;dev
              37636561366636643464376336303466613062633537323632306566653533383833366462366662
              6565353063303065303831323539656138653863353230620a653638643639333133306331336365
              62373737623337616130386137373461306535383538373162316263386165376131623631323434
              3866363862363335620a376466656164383032633338306162326639643635663936623939666238
              3161

You can add the output from any of the examples above to any playbook, variables file, or role for future use. Encrypted variables are larger than plain-text variables, but they protect your sensitive content while leaving the rest of the playbook, variables file, or role in plain text so you can easily read it.

Viewing encrypted variables
^^^^^^^^^^^^^^^^^^^^^^^^^^^

You can view the original value of an encrypted variable using the debug module. You must pass the password that was used to encrypt the variable. For example, if you stored the variable created by the last example above in a file called 'vars.yml', you could view the unencrypted value of that variable like this:

.. code-block:: console

   ansible localhost -m ansible.builtin.debug -a var="new_user_password" -e "@vars.yml" --vault-id dev@a_password_file

   localhost | SUCCESS => {
       "new_user_password": "hunter2"
   }


Encrypting files with Ansible Vault
-----------------------------------

Ansible Vault can encrypt any structured data file used by Ansible, including:

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

.. note::

	Ansible Vault uses an editor to create or modify encrypted files. See :ref:`vault_securing_editor` for some guidance on securing the editor.


Advantages and disadvantages of encrypting files
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

File-level encryption is easy to use. Password rotation for encrypted files is straightforward with the :ref:`rekey <rekeying_files>` command. Encrypting files can hide not only sensitive values, but the names of the variables you use. However, with file-level encryption the contents of files are no longer easy to access and read. This may be a problem with encrypted tasks files. When encrypting a variables file, see :ref:`tip_for_variables_and_vaults` for one way to keep references to these variables in a non-encrypted file. Ansible always decrypts the entire encrypted file when it is when loaded or referenced, because Ansible cannot know if it needs the content unless it decrypts it.

.. _creating_files:

Creating encrypted files
^^^^^^^^^^^^^^^^^^^^^^^^

To create a new encrypted data file called 'foo.yml' with the 'test' vault password from 'multi_password_file':

.. code-block:: bash

   ansible-vault create --vault-id test@multi_password_file foo.yml

The tool launches an editor (whatever editor you have defined with $EDITOR, default editor is vi). Add the content. When you close the editor session, the file is saved as encrypted data. The file header reflects the vault ID used to create it:

.. code-block:: text

   ``$ANSIBLE_VAULT;1.2;AES256;test``

To create a new encrypted data file with the vault ID 'my_new_password' assigned to it and be prompted for the password:

.. code-block:: bash

   ansible-vault create --vault-id my_new_password@prompt foo.yml

Again, add content to the file in the editor and save. Be sure to store the new password you created at the prompt, so you can find it when you want to decrypt that file.

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

To edit a file encrypted with the ``vault2`` password file and assigned the vault ID ``pass2``:

.. code-block:: bash

   ansible-vault edit --vault-id pass2@vault2 foo.yml


.. _rekeying_files:

Changing the password and/or vault ID on encrypted files
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To change the password on an encrypted file or files, use the :ref:`rekey <ansible_vault_rekey>` command:

.. code-block:: bash

    ansible-vault rekey foo.yml bar.yml baz.yml

This command can rekey multiple data files at once and will ask for the original password and also the new password. To set a different ID for the rekeyed files, pass the new ID to ``--new-vault-id``. For example, to rekey a list of files encrypted with the 'preprod1' vault ID from the 'ppold' file to the 'preprod2' vault ID and be prompted for the new password:

.. code-block:: bash

    ansible-vault rekey --vault-id preprod1@ppold --new-vault-id preprod2@prompt foo.yml bar.yml baz.yml


.. _decrypting_files:

Decrypting encrypted files
^^^^^^^^^^^^^^^^^^^^^^^^^^

If you have an encrypted file that you no longer want to keep encrypted, you can permanently decrypt it by running the :ref:`ansible-vault decrypt <ansible_vault_decrypt>` command. This command will save the file unencrypted to the disk, so be sure you do not want to :ref:`edit <ansible_vault_edit>` it instead.

.. code-block:: bash

    ansible-vault decrypt foo.yml bar.yml baz.yml


.. _vault_securing_editor:

Steps to secure your editor
^^^^^^^^^^^^^^^^^^^^^^^^^^^

Ansible Vault relies on your configured editor, which can be a source of disclosures. Most editors have ways to prevent loss of data, but these normally rely on extra plain text files that can have a clear text copy of your secrets. Consult your editor documentation to configure the editor to avoid disclosing secure data. The following sections provide some guidance on common editors but should not be taken as a complete guide to securing your editor.


vim
...

You can set the following ``vim`` options in command mode to avoid cases of disclosure. There may be more settings you need to modify to ensure security, especially when using plugins, so consult the ``vim`` documentation.


1. Disable swapfiles that act like an autosave in case of crash or interruption.

.. code-block:: text

  set noswapfile

2. Disable creation of backup files.

.. code-block:: text

  set nobackup
  set nowritebackup

3. Disable the viminfo file from copying data from your current session.

.. code-block:: text

  set viminfo=

4. Disable copying to the system clipboard.

.. code-block:: text

  set clipboard=


You can optionally add these settings in ``.vimrc`` for all files, or just specific paths or extensions. See the ``vim`` manual for details.


Emacs
......

You can set the following Emacs options to avoid cases of disclosure. There may be more settings you need to modify to ensure security, especially when using plugins, so consult the Emacs documentation.

1. Do not copy data to the system clipboard.

.. code-block:: text

  (setq x-select-enable-clipboard nil)

2. Disable creation of backup files.

.. code-block:: text

  (setq make-backup-files nil)

3. Disable autosave files.

.. code-block:: text

  (setq auto-save-default nil)
