Ansible Modules
===============

.. contents::
   :depth: 3

.. _modules_intro:

Introduction
````````````


Ansible ships with a number of modules (called the 'module library')
that can be executed directly on remote hosts or through :doc:`Playbooks <playbooks>`.
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

Documentation for each module can be accessed from the command line with the
ansible-doc as well as the man command::

    ansible-doc command

    man ansible.template

Let's see what's available in the Ansible module library, out of the box:


.. include:: modules/_list.rst

.. _ansible_doc:

Reading Module Documentation Locally
````````````````````````````````````

ansible-doc is a friendly command line tool that allows you to access module documentation locally.
It comes with Ansible.

To list documentation for a particular module::

   ansible-doc yum | less

To list all modules available::

   ansible-doc --list | less

To access modules outside of the stock module path (such as custom modules that live in your playbook directory), 
use the '--module-path' option to specify the directory where the module lives.

.. _writing_modules:

Writing your own modules
````````````````````````

See :doc:`developing_modules`.

.. seealso::

   :doc:`intro_adhoc`
       Examples of using modules in /usr/bin/ansible
   :doc:`playbooks`
       Examples of using modules with /usr/bin/ansible-playbook
   :doc:`developing_modules`
       How to write your own modules
   :doc:`developing_api`
       Examples of using modules with the Python API
   `Mailing List <http://groups.google.com/group/ansible-project>`_
       Questions? Help? Ideas?  Stop by the list on Google Groups
   `irc.freenode.net <http://irc.freenode.net>`_
       #ansible IRC chat channel

