Ansible Modules
===============

.. contents::
   :depth: 2
   :backlinks: top

Introduction
````````````


Ansible ships with a number of modules (called the 'module library')
that can be executed directly on remote hosts or through :doc:`playbooks`.
Users can also write their own modules.   These modules can control system
resources, like services, packages, or files (anything really), or
handle executing system commands.

Let's review how we execute three different modules from the command line::

    ansible webservers -m service -a "name=httpd state=running"
    ansible webservers -m ping
    ansible webservers -m command -a "/sbin/reboot -t now"

Each module supports taking arguments.  Nearly all modules take ``key=value``
arguments, space delimited.  Some modules take no arguments, and the
command/shell modules simply take the string of the command you want to run.

From playbooks, Ansible modules are executed in a very similar way::

    - name: reboot the servers
      action: command /sbin/reboot -t now

Version 0.8 and higher support the following shorter syntax::

    - name: reboot the servers
      command: /sbin/reboot -t now

All modules technically return JSON format data, though if you are using the
command line or playbooks, you don't really need to know much about
that.  If you're writing your own module, you care, and this means you do
not have to write modules in any particular language -- you get to choose.

Modules are `idempotent`, meaning they will seek to avoid changes to the system unless a change needs to be made.  When using Ansible
playbooks, these modules can trigger 'change events' in the form of notifying 'handlers'
to run additional tasks.

Let's see what's available in the Ansible module library, out of the box:


.. include:: modules/_list.rst


Writing your own modules
````````````````````````

See :doc:`moduledev`.

.. seealso::

   :doc:`contrib`
       User contributed playbooks, modules, and articles
   :doc:`examples`
       Examples of using modules in /usr/bin/ansible
   :doc:`playbooks`
       Examples of using modules with /usr/bin/ansible-playbook
   :doc:`moduledev`
       How to write your own modules
   :doc:`api`
       Examples of using modules with the Python API
   `Mailing List <http://groups.google.com/group/ansible-project>`_
       Questions? Help? Ideas?  Stop by the list on Google Groups
   `irc.freenode.net <http://irc.freenode.net>`_
       #ansible IRC chat channel

