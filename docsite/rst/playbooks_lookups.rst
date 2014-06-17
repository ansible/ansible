Using Lookups
=============

Lookup plugins allow access of data in Ansible from outside sources.  These plugins are evaluated on the Ansible control
machine, and can include reading the filesystem but also contacting external datastores and services.  
These values are then made available using the standard templating system
in Ansible, and are typically used to load variables or templates with information from those systems.

.. note:: This is considered an advanced feature, and many users will probably not rely on these features.  

.. note:: Lookups occur on the local computer, not on the remote computer.

.. contents:: Topics

.. _getting_file_contents:

Intro to Lookups: Getting File Contents
```````````````````````````````````````

The file lookup is the most basic lookup type.

Contents can be read off the filesystem as follows::

    - hosts: all
      vars:
         contents: "{{ lookup('file', '/etc/foo.txt') }}"

      tasks:

         - debug: msg="the value of foo.txt is {{ contents }}"

.. _password_lookup:

The Password Lookup
```````````````````

.. note::

    A great alternative to the password lookup plugin, if you don't need to generate random passwords on a per-host basis, would be to use :doc:`playbooks_vault`.  Read the documentation there and consider using it first, it will be more desirable for most applications.

``password`` generates a random plaintext password and stores it in
a file at a given filepath.  

(Docs about crypted save modes are pending)
 
If the file exists previously, it will retrieve its contents, behaving just like with_file. Usage of variables like "{{ inventory_hostname }}" in the filepath can be used to set
up random passwords per host (what simplifies password management in 'host_vars' variables).

Generated passwords contain a random mix of upper and lowercase ASCII letters, the
numbers 0-9 and punctuation (". , : - _"). The default length of a generated password is 20 characters.
This length can be changed by passing an extra parameter::

    ---
    - hosts: all

      tasks:

        # create a mysql user with a random password:
        - mysql_user: name={{ client }}
                      password="{{ lookup('password', 'credentials/' + client + '/' + tier + '/' + role + '/mysqlpassword length=15') }}"
                      priv={{ client }}_{{ tier }}_{{ role }}.*:ALL

        (...)

.. note:: If the file already exists, no data will be written to it. If the file has contents, those contents will be read in as the password. Empty files cause the password to return as an empty string        

Starting in version 1.4, password accepts a "chars" parameter to allow defining a custom character set in the generated passwords. It accepts comma separated list of names that are either string module attributes (ascii_letters,digits, etc) or are used literally::

    ---
    - hosts: all

      tasks:

        # create a mysql user with a random password using only ascii letters:
        - mysql_user: name={{ client }}
                      password="{{ lookup('password', '/tmp/passwordfile chars=ascii_letters') }}"
                      priv={{ client }}_{{ tier }}_{{ role }}.*:ALL

        # create a mysql user with a random password using only digits:
        - mysql_user: name={{ client }}
                      password="{{ lookup('password', '/tmp/passwordfile chars=digits') }}"
                      priv={{ client }}_{{ tier }}_{{ role }}.*:ALL

        # create a mysql user with a random password using many different char sets:
        - mysql_user: name={{ client }}
                      password="{{ lookup('password', '/tmp/passwordfile chars=ascii_letters,digits,hexdigits,punctuation') }}"
                      priv={{ client }}_{{ tier }}_{{ role }}.*:ALL

        (...)

To enter comma use two commas ',,' somewhere - preferably at the end. Quotes and double quotes are not supported.

.. _more_lookups:

More Lookups
````````````

.. note:: This feature is very infrequently used in Ansible.  You may wish to skip this section.

.. versionadded:: 0.8

Various *lookup plugins* allow additional ways to iterate over data.  In :doc:`Loops <playbooks_loops>` you will learn
how to use them to walk over collections of numerous types.  However, they can also be used to pull in data
from remote sources, such as shell commands or even key value stores. This section will cover lookup
plugins in this capacity.

Here are some examples::

    ---
    - hosts: all

      tasks:

         - debug: msg="{{ lookup('env','HOME') }} is an environment variable"

         - debug: msg="{{ item }} is a line from the result of this command"
           with_lines:
             - cat /etc/motd

         - debug: msg="{{ lookup('pipe','date') }} is the raw result of running this command"

         - debug: msg="{{ lookup('redis_kv', 'redis://localhost:6379,somekey') }} is value in Redis for somekey"

         - debug: msg="{{ lookup('dnstxt', 'example.com') }} is a DNS TXT record for example.com"

         - debug: msg="{{ lookup('template', './some_template.j2') }} is a value from evaluation of this template"

As an alternative you can also assign lookup plugins to variables or use them
elsewhere.  This macros are evaluated each time they are used in a task (or
template)::

    vars:
      motd_value: "{{ lookup('file', '/etc/motd') }}"

    tasks:

      - debug: msg="motd value is {{ motd_value }}"

.. seealso::

   :doc:`playbooks`
       An introduction to playbooks
   :doc:`playbooks_conditionals`
       Conditional statements in playbooks
   :doc:`playbooks_variables`
       All about variables
   :doc:`playbooks_loops`
       Looping in playbooks
   `User Mailing List <http://groups.google.com/group/ansible-devel>`_
       Have a question?  Stop by the google group!
   `irc.freenode.net <http://irc.freenode.net>`_
       #ansible IRC chat channel



