.. _working_with_modules:

Working With Modules
====================

.. toctree::
   :maxdepth: 1

   modules_intro
   common_return_values
   modules_support
   ../modules/modules_by_category


Ansible ships with a number of modules (called the 'module library')
that can be executed directly on remote hosts or through :doc:`Playbooks <playbooks>`.

Users can also write their own modules. These modules can control system resources,
like services, packages, or files (anything really), or handle executing system commands.


.. seealso::

   :doc:`intro_adhoc`
       Examples of using modules in /usr/bin/ansible
   :doc:`playbooks`
       Examples of using modules with /usr/bin/ansible-playbook
   :doc:`../dev_guide/developing_modules`
       How to write your own modules
   :doc:`../dev_guide/developing_api`
       Examples of using modules with the Python API
   `Mailing List <http://groups.google.com/group/ansible-project>`_
       Questions? Help? Ideas?  Stop by the list on Google Groups
   `irc.freenode.net <http://irc.freenode.net>`_
       #ansible IRC chat channel
