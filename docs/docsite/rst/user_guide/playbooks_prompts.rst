Prompts
=======

When running a playbook, you may wish to prompt the user for certain input, and can
do so with the 'vars_prompt' section.

A common use for this might be for asking for sensitive data that you do not want to record.

This has uses beyond security, for instance, you may use the same playbook for all
software releases and would prompt for a particular release version
in a push-script.

Here is a most basic example::

    ---
    - hosts: all
      vars_prompt:

        - name: username
          prompt: "What is your username?"
          private: no

        - name: password
          prompt: "What is your password?"

      tasks:

        - debug:
            msg: 'Logging in as {{ username }}'

The user input is hidden by default but it can be made visible by setting ``private: no``.

.. note::
    Prompts for individual ``vars_prompt`` variables will be skipped for any variable that is already defined through the command line ``--extra-vars`` option, or when running from a non-interactive session (such as cron or Ansible Tower). See :ref:`passing_variables_on_the_command_line` in the /Variables/ chapter.

If you have a variable that changes infrequently, it might make sense to
provide a default value that can be overridden. This can be accomplished using
the default argument::

   vars_prompt:

     - name: "release_version"
       prompt: "Product release version"
       default: "1.0"

If `Passlib <https://passlib.readthedocs.io/en/stable/>`_ is installed, vars_prompt can also encrypt the
entered value so you can use it, for instance, with the user module to define a password::

   vars_prompt:

     - name: "my_password2"
       prompt: "Enter password2"
       private: yes
       encrypt: "sha512_crypt"
       confirm: yes
       salt_size: 7

You can use any crypt scheme supported by 'Passlib':

- *des_crypt* - DES Crypt
- *bsdi_crypt* - BSDi Crypt
- *bigcrypt* - BigCrypt
- *crypt16* - Crypt16
- *md5_crypt* - MD5 Crypt
- *bcrypt* - BCrypt
- *sha1_crypt* - SHA-1 Crypt
- *sun_md5_crypt* - Sun MD5 Crypt
- *sha256_crypt* - SHA-256 Crypt
- *sha512_crypt* - SHA-512 Crypt
- *apr_md5_crypt* - Apache's MD5-Crypt variant
- *phpass* - PHPass' Portable Hash
- *pbkdf2_digest* - Generic PBKDF2 Hashes
- *cta_pbkdf2_sha1* - Cryptacular's PBKDF2 hash
- *dlitz_pbkdf2_sha1* - Dwayne Litzenberger's PBKDF2 hash
- *scram* - SCRAM Hash
- *bsd_nthash* - FreeBSD's MCF-compatible nthash encoding

However, the only parameters accepted are 'salt' or 'salt_size'. You can use your own salt using
'salt', or have one generated automatically using 'salt_size'. If nothing is specified, a salt
of size 8 will be generated.

.. versionadded:: 2.7

When Passlib is not installed the `crypt <https://docs.python.org/2/library/crypt.html>`_ library is used as fallback.
Depending on your platform at most the following crypt schemes are supported:

- *bcrypt* - BCrypt
- *md5_crypt* - MD5 Crypt
- *sha256_crypt* - SHA-256 Crypt
- *sha512_crypt* - SHA-512 Crypt

.. versionadded:: 2.8

If you need to put in special characters (i.e `{%`) that might create templating errors, use the ``unsafe`` option::

   vars_prompt:
     - name: "my_password_with_weird_chars"
       prompt: "Enter password"
       unsafe: yes
       private: yes

.. seealso::

   :ref:`playbooks_intro`
       An introduction to playbooks
   :ref:`playbooks_conditionals`
       Conditional statements in playbooks
   :ref:`playbooks_variables`
       All about variables
   `User Mailing List <https://groups.google.com/group/ansible-devel>`_
       Have a question?  Stop by the google group!
   `irc.libera.chat <https://libera.chat/>`_
       #ansible IRC chat channel
