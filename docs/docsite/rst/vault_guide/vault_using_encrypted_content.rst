.. _vault_using_encrypted_content:
.. _playbooks_vault:
.. _providing_vault_passwords:

Using encrypted variables and files
===================================

When you run a task or playbook that uses encrypted variables or files, you must provide the passwords to decrypt the variables or files. You can do this at the command line or by setting a default password source in a config option or an environment variable.

Passing a single password
-------------------------

If all the encrypted variables and files your task or playbook needs use a single password, you can use the :option:`--ask-vault-pass <ansible-playbook --ask-vault-pass>` or :option:`--vault-password-file <ansible-playbook --vault-password-file>` cli options.

To prompt for the password:

.. code-block:: bash

    ansible-playbook --ask-vault-pass site.yml

To retrieve the password from the :file:`/path/to/my/vault-password-file` file:

.. code-block:: bash

    ansible-playbook --vault-password-file /path/to/my/vault-password-file site.yml

To get the password from the vault password client script :file:`my-vault-password-client.py`:

.. code-block:: bash

    ansible-playbook --vault-password-file my-vault-password-client.py


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

To get the password for the 'dev' vault ID from the vault password client script :file:`my-vault-password-client.py`:

.. code-block:: bash

    ansible-playbook --vault-id dev@my-vault-password-client.py

Passing multiple vault passwords
--------------------------------

If your task or playbook requires multiple encrypted variables or files that you encrypted with different vault IDs, you must use the :option:`--vault-id <ansible-playbook --vault-id>` option, passing multiple ``--vault-id`` options to specify the vault IDs ('dev', 'prod', 'cloud', 'db') and sources for the passwords (prompt, file, script). . For example, to use a 'dev' password read from a file and to be prompted for the 'prod' password:

.. code-block:: bash

    ansible-playbook --vault-id dev@dev-password --vault-id prod@prompt site.yml

By default the vault ID labels (dev, prod and so on) are only hints. Ansible attempts to decrypt vault content with each password. The password with the same label as the encrypted data will be tried first, after that each vault secret will be tried in the order they were provided on the command line.

Where the encrypted data has no label, or the label does not match any of the provided labels, the passwords will be tried in the order they are specified. In the example above, the 'dev' password will be tried first, then the 'prod' password for cases where Ansible doesn't know which vault ID is used to encrypt something.

Using ``--vault-id`` without a vault ID
---------------------------------------

The :option:`--vault-id <ansible-playbook --vault-id>` option can also be used without specifying a vault-id. This behavior is equivalent to :option:`--ask-vault-pass <ansible-playbook --ask-vault-pass>` or :option:`--vault-password-file <ansible-playbook --vault-password-file>` so is rarely used.

For example, to use a password file :file:`dev-password`:

.. code-block:: bash

    ansible-playbook --vault-id dev-password site.yml

To prompt for the password:

.. code-block:: bash

    ansible-playbook --vault-id @prompt site.yml

To get the password from an executable script :file:`my-vault-password-client.py`:

.. code-block:: bash

    ansible-playbook --vault-id my-vault-password-client.py

Configuring defaults for using encrypted content
================================================

Setting a default vault ID
--------------------------

If you use one vault ID more frequently than any other, you can set the config option :ref:`DEFAULT_VAULT_IDENTITY_LIST` to specify a default vault ID and password source. Ansible will use the default vault ID and source any time you do not specify :option:`--vault-id <ansible-playbook --vault-id>`. You can set multiple values for this option. Setting multiple values is equivalent to passing multiple :option:`--vault-id <ansible-playbook --vault-id>` cli options.

Setting a default password source
---------------------------------

If you don't want to provide the password file on the command line or if you use one vault password file more frequently than any other, you can set the :ref:`DEFAULT_VAULT_PASSWORD_FILE` config option or the :envvar:`ANSIBLE_VAULT_PASSWORD_FILE` environment variable to specify a default file to use. For example, if you set ``ANSIBLE_VAULT_PASSWORD_FILE=~/.vault_pass.txt``, Ansible will automatically search for the password in that file. This is useful if, for example, you use Ansible from a continuous integration system such as Jenkins.

The file that you reference can be either a file containing the password (in plain text), or it can be a script (with executable permissions set) that returns the password.

When are encrypted files made visible?
======================================

In general, content you encrypt with Ansible Vault remains encrypted after execution. However, there is one exception. If you pass an encrypted file as the ``src`` argument to the :ref:`copy <copy_module>`, :ref:`template <template_module>`, :ref:`unarchive <unarchive_module>`, :ref:`script <script_module>` or :ref:`assemble <assemble_module>` module, the file will not be encrypted on the target host (assuming you supply the correct vault password when you run the play). This behavior is intended and useful. You can encrypt a configuration file or template to avoid sharing the details of your configuration, but when you copy that configuration to servers in your environment, you want it to be decrypted so local users and processes can access it.

.. _vault_format:

Format of files encrypted with Ansible Vault
============================================

Ansible Vault creates UTF-8 encoded txt files. The file format includes a newline terminated header. For example:

 .. code-block:: text

    $ANSIBLE_VAULT;1.1;AES256

or

 .. code-block:: text

    $ANSIBLE_VAULT;1.2;AES256;vault-id-label

The header contains up to four elements, separated by semi-colons (``;``).

  1. The format ID (``$ANSIBLE_VAULT``). Currently ``$ANSIBLE_VAULT`` is the only valid format ID. The format ID identifies content that is encrypted with Ansible Vault (via vault.is_encrypted_file()).

  2. The vault format version (``1.X``). All supported versions of Ansible will currently default to '1.1' or '1.2' if a labeled vault ID is supplied. The '1.0' format is supported for reading only (and will be converted automatically to the '1.1' format on write). The format version is currently used as an exact string compare only (version numbers are not currently 'compared').

  3. The cipher algorithm used to encrypt the data (``AES256``). Currently ``AES256`` is the only supported cipher algorithm. Vault format 1.0 used 'AES', but current code always uses 'AES256'.

  4. The vault ID label used to encrypt the data (optional, ``vault-id-label``) For example, if you encrypt a file with ``--vault-id dev@prompt``, the vault-id-label is ``dev``.

Note: In the future, the header could change. Fields after the format ID and format version depend on the format version, and future vault format versions may add more cipher algorithm options and/or additional fields.

The rest of the content of the file is the 'vaulttext'. The vaulttext is a text armored version of the
encrypted ciphertext. Each line is 80 characters wide, except for the last line which may be shorter.

Ansible Vault payload format 1.1 - 1.2
--------------------------------------

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
