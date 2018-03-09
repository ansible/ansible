.. _playbooks_vault:

Using Vault in playbooks
========================

.. contents:: Topics

The "Vault" is a feature of Ansible that allows you to keep sensitive data such as passwords or keys in encrypted files, rather than as plaintext in playbooks or roles. These vault files can then be distributed or placed in source control.

To enable this feature, a command line tool, :ref:`ansible-vault` is used to edit files, and a command line flag :option:`--ask-vault-pass <ansible-vault --ask-vault-pass>` or :option:`--vault-password-file <ansible-vault --vault-password-file>` is used. You can also modify your ``ansible.cfg`` file to specify the location of a password file or configure Ansible to always prompt for the password. These options require no command line flag usage.

For best practices advice, refer to :ref:`best_practices_for_variables_and_vaults`.

.. _running_a_playbook_with_vault:

Running a Playbook With Vault
`````````````````````````````

To run a playbook that contains vault-encrypted data files, you must pass one of two flags.  To specify the vault-password interactively::

    ansible-playbook site.yml --ask-vault-pass

This prompt will then be used to decrypt (in memory only) any vault encrypted files that are accessed.  Currently this requires that all files be encrypted with the same password.

Alternatively, passwords can be specified with a file or a script (the script version will require Ansible 1.7 or later).  When using this flag, ensure permissions on the file are such that no one else can access your key and do not add your key to source control::

    ansible-playbook site.yml --vault-password-file ~/.vault_pass.txt

    ansible-playbook site.yml --vault-password-file ~/.vault_pass.py

The password should be a string stored as a single line in the file.

.. note::
   You can also set :envvar:`ANSIBLE_VAULT_PASSWORD_FILE` environment variable, e.g. ``ANSIBLE_VAULT_PASSWORD_FILE=~/.vault_pass.txt`` and Ansible will automatically search for the password in that file.

If you are using a script instead of a flat file, ensure that it is marked as executable, and that the password is printed to standard output.  If your script needs to prompt for data, prompts can be sent to standard error.

This is something you may wish to do if using Ansible from a continuous integration system like Jenkins.

The :option:`--vault-password-file <ansible-pull --vault-password-file>` option can also be used with the :ref:`ansible-pull` command if you wish, though this would require distributing the keys to your nodes, so understand the implications -- vault is more intended for push mode.


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


.. _encrypt_string:

Using encrypt_string
````````````````````

This command will output a string in the above format ready to be included in a YAML file.
The string to encrypt can be provided via stdin, command line arguments, or via an interactive prompt.

See :ref:`encrypt_string_for_use_in_yaml`.
