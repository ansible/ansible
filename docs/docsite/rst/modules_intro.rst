Introduction
============

Modules (also referred to as "task plugins" or "library plugins") are the ones that do
the actual work in ansible, they are what gets executed in each playbook task.
But you can also run a single one using the 'ansible' command.

Let's review how we execute three different modules from the command line::

    ansible webservers -m service -a "name=httpd state=started"
    ansible webservers -m ping
    ansible webservers -m command -a "/sbin/reboot -t now"

Each module supports taking arguments.  Nearly all modules take ``key=value``
arguments, space delimited.  Some modules take no arguments, and the command/shell modules simply
take the string of the command you want to run.

From playbooks, Ansible modules are executed in a very similar way::

    - name: reboot the servers
      action: command /sbin/reboot -t now

Which can be abbreviated to::

    - name: reboot the servers
      command: /sbin/reboot -t now

Another way to pass arguments to a module is using yaml syntax also called 'complex args' ::

    - name: restart webserver
      service:
        name: httpd
        state: restarted

All modules technically return JSON format data, though if you are using the command line or playbooks, you don't really need to know much about
that.  If you're writing your own module, you care, and this means you do not have to write modules in any particular language -- you get to choose.

Modules should be idempotent, and should avoid making any changes if
they detect that the current state matches the desired final state. When using
Ansible playbooks, these modules can trigger 'change events' in the form of
notifying 'handlers' to run additional tasks.

Documentation for each module can be accessed from the command line with the ansible-doc tool::

    ansible-doc yum

A list of all installed modules is also available::

    ansible-doc -l

Module Paths
````````````

Ansible can discover modules in several locations. 

**Relative to Playbooks**

The easiest way to include a module is by adding a ``library`` folder to your project 
relative to your playbooks. Module files (.py, etc.) can be added there.

The structure will look like this::

    ├── playbook.yml
    └── library
        ├── my_module.py
        └── my_other_module.py

.. note::

    Currently Ansible does not support organizing modules into sub-folders under the ``library``
    folder.
    
**Inside a Role**

The library folder can also exist within a role following the same layout above.

The structure would look like this for a "webservers" role::

    └── roles
        └── webservers
            ├── tasks
            ├── vars
            ├── ...
            └── library
                ├── my_module.py
                └── my_other_module.py

**Ansible Configuration File**

In the Ansible configuration file you can modify the `library <http://docs.ansible.com/ansible/intro_configuration.html#library>`_
setting to add additional module search paths.

**Environment & Command-Line**

You can specify additional module paths using the ``--module-path`` command-line option. You may also 
specify paths in the :envvar:`ANSIBLE_LIBRARY` environment variable. 

.. seealso::

   :doc:`intro_adhoc`
       Examples of using modules in /usr/bin/ansible
   :doc:`playbooks`
       Examples of using modules with /usr/bin/ansible-playbook
   :doc:`dev_guide/developing_modules`
       How to write your own modules
   :doc:`dev_guide/developing_api`
       Examples of using modules with the Python API
   `Mailing List <http://groups.google.com/group/ansible-project>`_
       Questions? Help? Ideas?  Stop by the list on Google Groups
   `irc.freenode.net <http://irc.freenode.net>`_
       #ansible IRC chat channel

