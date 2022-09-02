.. _vault_managing_passwords:

Managing vault passwords
========================

Managing your encrypted content is easier if you develop a strategy for managing your vault passwords. A vault password can be any string you choose. There is no special command to create a vault password. However, you need to keep track of your vault passwords. Each time you encrypt a variable or file with Ansible Vault, you must provide a password. When you use an encrypted variable or file in a command or playbook, you must provide the same password that was used to encrypt it. To develop a strategy for managing vault passwords, start with two questions:

  * Do you want to encrypt all your content with the same password, or use different passwords for different needs?
  * Where do you want to store your password or passwords?

Choosing between a single password and multiple passwords
---------------------------------------------------------

If you have a small team or few sensitive values, you can use a single password for everything you encrypt with Ansible Vault. Store your vault password securely in a file or a secret manager as described below.

If you have a larger team or many sensitive values, you can use multiple passwords. For example, you can use different passwords for different users or different levels of access. Depending on your needs, you might want a different password for each encrypted file, for each directory, or for each environment. For example, you might have a playbook that includes two vars files, one for the dev environment and one for the production environment, encrypted with two different passwords. When you run the playbook, select the correct vault password for the environment you are targeting, using a vault ID.

.. _vault_ids:

Managing multiple passwords with vault IDs
------------------------------------------

If you use multiple vault passwords, you can differentiate one password from another with vault IDs. You use the vault ID in three ways:

  * Pass it with :option:`--vault-id <ansible-playbook --vault-id>` to the :ref:`ansible-vault` command when you create encrypted content
  * Include it wherever you store the password for that vault ID (see :ref:`storing_vault_passwords`)
  * Pass it with :option:`--vault-id <ansible-playbook --vault-id>` to the :ref:`ansible-playbook` command when you run a playbook that uses content you encrypted with that vault ID

When you pass a vault ID as an option to the :ref:`ansible-vault` command, you add a label (a hint or nickname) to the encrypted content. This label documents which password you used to encrypt it. The encrypted variable or file includes the vault ID label in plain text in the header. The vault ID is the last element before the encrypted content. For example:

 .. code-block:: yaml

    my_encrypted_var: !vault |
              $ANSIBLE_VAULT;1.2;AES256;dev
              30613233633461343837653833666333643061636561303338373661313838333565653635353162
              3263363434623733343538653462613064333634333464660a663633623939393439316636633863
              61636237636537333938306331383339353265363239643939666639386530626330633337633833
              6664656334373166630a363736393262666465663432613932613036303963343263623137386239
              6330

In addition to the label, you must provide a source for the related password. The source can be a prompt, a file, or a script, depending on how you are storing your vault passwords. The pattern looks like this:

.. code-block:: bash

   --vault-id label@source

If your playbook uses multiple encrypted variables or files that you encrypted with different passwords, you must pass the vault IDs when you run that playbook. You can use :option:`--vault-id <ansible-playbook --vault-id>` by itself, with :option:`--vault-password-file <ansible-playbook --vault-password-file>`, or with :option:`--ask-vault-pass <ansible-playbook --ask-vault-pass>`. The pattern is the same as when you create encrypted content: include the label and the source for the matching password.

See below for examples of encrypting content with vault IDs and using content encrypted with vault IDs. The :option:`--vault-id <ansible-playbook --vault-id>` option works with any Ansible command that interacts with vaults, including :ref:`ansible-vault`, :ref:`ansible-playbook`, and so on.

Limitations of vault IDs
^^^^^^^^^^^^^^^^^^^^^^^^

Ansible does not enforce using the same password every time you use a particular vault ID label. You can encrypt different variables or files with the same vault ID label but different passwords. This usually happens when you type the password at a prompt and make a mistake. It is possible to use different passwords with the same vault ID label on purpose. For example, you could use each label as a reference to a class of passwords, rather than a single password. In this scenario, you must always know which specific password or file to use in context. However, you are more likely to encrypt two files with the same vault ID label and different passwords by mistake. If you encrypt two files with the same label but different passwords by accident, you can :ref:`rekey <rekeying_files>` one file to fix the issue.

Enforcing vault ID matching
^^^^^^^^^^^^^^^^^^^^^^^^^^^

By default the vault ID label is only a hint to remind you which password you used to encrypt a variable or file. Ansible does not check that the vault ID in the header of the encrypted content matches the vault ID you provide when you use the content. Ansible decrypts all files and variables called by your command or playbook that are encrypted with the password you provide. To check the encrypted content and decrypt it only when the vault ID it contains matches the one you provide with ``--vault-id``, set the config option :ref:`DEFAULT_VAULT_ID_MATCH`. When you set :ref:`DEFAULT_VAULT_ID_MATCH`, each password is only used to decrypt data that was encrypted with the same label. This is efficient, predictable, and can reduce errors when different values are encrypted with different passwords.

.. note::
   Even with the :ref:`DEFAULT_VAULT_ID_MATCH` setting enabled, Ansible does not enforce using the same password every time you use a particular vault ID label.

.. _storing_vault_passwords:

Storing and accessing vault passwords
-------------------------------------

You can memorize your vault password, or manually copy vault passwords from any source and paste them at a command-line prompt, but most users store them securely and access them as needed from within Ansible. You have two options for storing vault passwords that work from within Ansible: in files, or in a third-party tool such as the system keyring or a secret manager. If you store your passwords in a third-party tool, you need a vault password client script to retrieve them from within Ansible.

Storing passwords in files
^^^^^^^^^^^^^^^^^^^^^^^^^^

To store a vault password in a file, enter the password as a string on a single line in the file. Make sure the permissions on the file are appropriate. Do not add password files to source control.

.. _vault_password_client_scripts:

Storing passwords in third-party tools with vault password client scripts
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

You can store your vault passwords on the system keyring, in a database, or in a secret manager and retrieve them from within Ansible using a vault password client script. Enter the password as a string on a single line. If your password has a vault ID, store it in a way that works with your password storage tool.

To create a vault password client script:

  * Create a file with a name ending in either ``-client`` or ``-client.EXTENSION``
  * Make the file executable
  * Within the script itself:
      * Print the passwords to standard output
      * Accept a ``--vault-id`` option
      * If the script prompts for data (for example, a database password), display the prompts to the TTY.

When you run a playbook that uses vault passwords stored in a third-party tool, specify the script as the source within the ``--vault-id`` flag. For example:

.. code-block:: bash

    ansible-playbook --vault-id dev@contrib/vault/vault-keyring-client.py

Ansible executes the client script with a ``--vault-id`` option so the script knows which vault ID label you specified. For example a script loading passwords from a secret manager can use the vault ID label to pick either the 'dev' or 'prod' password. The example command above results in the following execution of the client script:

.. code-block:: bash

    contrib/vault/vault-keyring-client.py --vault-id dev

For an example of a client script that loads passwords from the system keyring, see the `vault-keyring-client script <https://github.com/ansible-community/contrib-scripts/blob/main/vault/vault-keyring-client.py>`_.