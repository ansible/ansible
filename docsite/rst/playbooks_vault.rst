Vault
=====

.. contents:: Topics

New in Ansible 1.5, "Vault" is a feature of ansible that allows keeping encrypted data in source control.

To enable this feature, a command line tool, `ansible-vault` is used to edit files, and a command line flag `--ask-vault-pass` or `--vault-password-file` is used.

.. _what_can_be_encrypted_with_vault:

What Can Be Encrypted With Vault
````````````````````````````````

The vault feature can encrypt any structured data file used by Ansible.  This can include "group_vars/" or "host_vars/" inventory variables, variables loaded by "include_vars" or "vars_files", or variable files passed on the ansible-playbook command line with "-e @file.yml" or "-e @file.json".  Role variables and defaults are also included!

Because Ansible tasks, handlers, and so on are also data, these can also be encrypted with vault.  If you'd like to not betray what variables you are even using, you can go as far to keep an individual task file entirely encrypted.  However, that might be a little much and could annoy your coworkers :)

.. _creating_files:

Creating Encrypted Files
````````````````````````

To create a new encrypted data file, run the following command::

   ansible-vault create foo.yml

First you will be prompted for a password.  The password used with vault currently must be the same for all files you wish to use together at the same time.

After providing a password, the tool will launch whatever editor you have defined with $EDITOR, and defaults to vim.  Once you are done with the editor session, the file will be saved as encrypted data.

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

.. _running_a_playbook_with_vault:

Running a Playbook With Vault
`````````````````````````````

To run a playbook that contains vault-encrypted data files, you must pass one of two flags.  To specify the vault-password interactively::

    ansible-playbook site.yml --ask-vault-pass

This prompt will then be used to decrypt (in memory only) any vault encrypted files that are accessed.  Currently this requires that all passwords be encrypted with the same password.

Alternatively, passwords can be specified with a file.  If this is done, be careful to ensure permissions on the file are such that no one else can access your key, and do not add your key to source control::

    ansible-playbook site.yml --vault-password-file ~/.vault_pass.txt

The password should be a string stored as a single line in the file.

This is likely something you may wish to do if using Ansible from a continuous integration system like Jenkins.

(The `--vault-password-file` option can also be used with the :ref:`ansible-pull` command if you wish, though this would require distributing the keys to your nodes, so understand the implications -- vault is more intended for push mode).

.. _gpg_support:

Enable GPG support
``````````````````

By default ansible-vault operates in a pre-shared key mode implementing the AES256 cipher to provide encryption for file contents. Using GPG over AES256 allows an encrypted file to be shared among a number of users while not needing to share passwords.

The default cipher can be changed via settings in `ansible.cfg`. You MUST also specify a list of trusted public key ids to use for encryption::

    [vault]
    cipher = GPG
    gpg_recipients = 895276B5 C5864A29

To migrate files from AES256 to GPG cipher type you will first need to use `ansible-vault decrypt`, then modify your `ansible.cfg` and finally run `ansible-vault encrypt`.

Compatability
^^^^^^^^^^^^^

When using `ansible-vault` with GPG you must have the following packages installed::

    # RHEL 6 (via EPEL) and Fedora
    gnupg
    python-gnupg

Alternatively the `gnupg wrapper <http://pythonhosted.org/python-gnupg/>`_ can be installed via pip::

    pip install python-gnupg

Using the gpg-agent
^^^^^^^^^^^^^^^^^^^

If you wish to leverage the systems gpg-agent for password caching you can uncomment the gpg_noprompt directive with `ansible.cfg`::

    [vault]
    cipher = GPG
    gpg_recipients = 895276B5 C5864A29
    gpg_noprompt = True

When gpg_noprompt is set the builtin ansible-vault passphrase prompt is surpressed. Be aware that without a workaround this will lead to a deadlock due to upstream issues in the python-gnupg wrapper. To resolve this you can add the following to you .bashrc (or similar) to load the keys into the gpg-agent prior to ansible-vault requiring them.

Firstly create an blank document which will be decrypted first::

    touch /path/to/ansible-vault-gpg
    gpg -e -a -r [YOUR KEY ID] /path/to/ansible-vault-gpg

Secondly install the shell functions to ensure calls which require decryption are first checked against our test file::

    function ansible-vault() {
    gpg --batch -d /path/to/ansible-vault-gpg.asc >/dev/null 2>&1
    rc=$?
    if [ $rc -eq 0 ]; then
    /path/to/bin/ansible-vault "$@"
    else
    echo "Failed to decrypt test file, check your system GPG and gpg-agent"
    fi
    }
    function ansible-playbook() {
    gpg --batch -d /path/to/ansible-vault-gpg.asc >/dev/null 2>&1
    rc=$?
    if [ $rc -eq 0 ]; then
    /path/to/bin/ansible-playbook "$@"
    else
    echo "Failed to decrypt test file, check your system GPG and gpg-agent"
    fi
    }

The end result here is that on first use your shell will correctly trigger the askpass program and unlock your private key via gpg-agent. When the subsequent request from to decrypt arrives from ansible-vault your decryption will occur without a passphrase prompt.
