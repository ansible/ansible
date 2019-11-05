.. _playbooks_vault:

Using Vault in playbooks
========================

.. contents:: Topics

The "Vault" is a feature of Ansible that allows you to keep sensitive data such as passwords or keys protected at rest, rather than as plaintext in playbooks or roles. These vaults can then be distributed or placed in source control.

There are 2 types of vaulted content and each has their own uses and limitations:

:Vaulted files:
    * The full file is encrypted in the vault, this can contain Ansible variables or any other type of content.
    * It will always be decrypted when loaded or referenced, Ansible cannot know if it needs the content unless it decrypts it.
    * It can be used for inventory, anything that loads variables (i.e vars_files, group_vars, host_vars, include_vars, etc)
      and some actions that deal with files (i.e M(copy), M(assemble), M(script), etc).

:Single encrypted variable:
    * Only specific variables are encrypted inside a normal 'variable file'.
    * Does not work for other content, only variables.
    * Decrypted on demand, so you can have vaulted variables with different vault secrets and only provide those needed.
    * You can mix vaulted and non vaulted variables in the same file, even inline in a play or role.

.. warning::
    * Vault ONLY protects data 'at rest'.  Once decrypted, play and plugin authors are responsible for avoiding any secret disclosure,
      see :ref:`no_log <keep_secret_data>` for details on hiding output.

To enable this feature, a command line tool, :ref:`ansible-vault` is used to edit files, and a command line flag :option:`--ask-vault-pass <ansible-vault-create --ask-vault-pass>`, :option:`--vault-password-file <ansible-vault-create --vault-password-file>` or :option:`--vault-id <ansible-playbook --vault-id>` is used. You can also modify your ``ansible.cfg`` file to specify the location of a password file or configure Ansible to always prompt for the password. These options require no command line flag usage.

For best practices advice, refer to :ref:`best_practices_for_variables_and_vaults`.

Running a Playbook With Vault
`````````````````````````````

To run a playbook that contains vault-encrypted data files, you must provide the vault password.

To specify the vault-password interactively::

    ansible-playbook site.yml --ask-vault-pass

This prompt will then be used to decrypt (in memory only) any vault encrypted files that are accessed.

Alternatively, passwords can be specified with a file or a script (the script version will require Ansible 1.7 or later).  When using this flag, ensure permissions on the file are such that no one else can access your key and do not add your key to source control::

    ansible-playbook site.yml --vault-password-file ~/.vault_pass.txt

    ansible-playbook site.yml --vault-password-file ~/.vault_pass.py

The password should be a string stored as a single line in the file.

If you are using a script instead of a flat file, ensure that it is marked as executable, and that the password is printed to standard output.  If your script needs to prompt for data, prompts can be sent to standard error.

.. note::
   You can also set :envvar:`ANSIBLE_VAULT_PASSWORD_FILE` environment variable, e.g. ``ANSIBLE_VAULT_PASSWORD_FILE=~/.vault_pass.txt`` and Ansible will automatically search for the password in that file.

   This is something you may wish to do if using Ansible from a continuous integration system like Jenkins.

The :option:`--vault-password-file <ansible-pull --vault-password-file>` option can also be used with the :ref:`ansible-pull` command if you wish, though this would require distributing the keys to your nodes, so understand the implications -- vault is more intended for push mode.


Multiple Vault Passwords
````````````````````````

Ansible 2.4 and later support the concept of multiple vaults that are encrypted with different passwords
Different vaults can be given a label to distinguish them (generally values like dev, prod etc.).

The :option:`--ask-vault-pass <ansible-playbook --ask-vault-pass>` and
:option:`--vault-password-file <ansible-playbook --vault-password-file>` options can be used as long as
only a single password is needed for any given run.

Alternatively the :option:`--vault-id <ansible-playbook --vault-id>` option can be used to provide the
password and indicate which vault label it's for. This can be clearer when multiple vaults are used within
a single inventory. For example:

To be prompted for the 'dev' password:

.. code-block:: bash

    ansible-playbook site.yml --vault-id dev@prompt

To get the 'dev' password from a file or script:

.. code-block:: bash

    ansible-playbook site.yml --vault-id dev@~/.vault_pass.txt

    ansible-playbook site.yml --vault-id dev@~/.vault_pass.py

If multiple vault passwords are required for a single run, :option:`--vault-id <ansible-playbook --vault-id>` must
be used as it can be specified multiple times to provide the multiple passwords.  For example:

To read the 'dev' password from a file and prompt for the 'prod' password:

.. code-block:: bash

    ansible-playbook site.yml --vault-id dev@~/.vault_pass.txt --vault-id prod@prompt

The :option:`--ask-vault-pass <ansible-playbook --ask-vault-pass>` or
:option:`--vault-password-file <ansible-playbook --vault-password-file>` options can be used to specify one of
the passwords, but it's generally cleaner to avoid mixing these with :option:`--vault-id <ansible-playbook --vault-id>`.

.. note::
    By default the vault label (dev, prod etc.) is just a hint. Ansible will try to decrypt each
    vault with every provided password.

    Setting the config option :ref:`DEFAULT_VAULT_ID_MATCH` will change this behavior so that each password
    is only used to decrypt data that was encrypted with the same label. See :ref:`specifying_vault_ids`
    for more details.

Vault Password Client Scripts
`````````````````````````````

Ansible 2.5 and later support using a single executable script to get different passwords depending on the
vault label. These client scripts must have a file name that ends with :file:`-client`. For example:

To get the dev password from the system keyring using the :file:`contrib/vault/vault-keyring-client.py` script:

.. code-block:: bash

    ansible-playbook --vault-id dev@contrib/vault/vault-keyring-client.py

See :ref:`vault_password_client_scripts` for a complete explanation of this topic.


.. _single_encrypted_variable:

Single Encrypted Variable
`````````````````````````

As of version 2.3, Ansible can now use a vaulted variable that lives in an otherwise 'clear text' YAML file::

    notsecret: myvalue
    mysecret: !vault |
              $ANSIBLE_VAULT;1.1;AES256
              66386439653236336462626566653063336164663966303231363934653561363964363833313662
              6431626536303530376336343832656537303632313433360a626438346336353331386135323734
              62656361653630373231613662633962316233633936396165386439616533353965373339616234
              3430613539666330390a313736323265656432366236633330313963326365653937323833366536
              34623731376664623134383463316265643436343438623266623965636363326136
    other_plain_text: othervalue

To create a vaulted variable, use the :ref:`ansible-vault encrypt_string <ansible_vault_encrypt_string>` command. See :ref:`encrypt_string` for details.

This vaulted variable will be decrypted with the supplied vault secret and used as a normal variable. The ``ansible-vault`` command line supports stdin and stdout for encrypting data on the fly, which can be used from your favorite editor to create these vaulted variables; you just have to be sure to add the ``!vault`` tag so both Ansible and YAML are aware of the need to decrypt. The ``|`` is also required, as vault encryption results in a multi-line string.

.. note::
   Inline vaults ONLY work on variables, you cannot use directly on a task's options.

.. _encrypt_string:

Using encrypt_string
````````````````````

This command will output a string in the above format ready to be included in a YAML file.
The string to encrypt can be provided via stdin, command line arguments, or via an interactive prompt.

See :ref:`encrypt_string_for_use_in_yaml`.
