Developing Modules
==================

.. contents:: Topics

.. _module_dev_welcome:

Welcome
```````
This section discusses how to develop, debug, review, and test modules.


Ansible modules are reusable, standalone scripts that can be used by the Ansible API,
or by the :command:`ansible` or :command:`ansible-playbook` programs.  They
return information to ansible by printing a JSON string to stdout before
exiting.  They take arguments in in one of several ways which we'll go into
as we work through this tutorial.

See :doc:`../modules` for a list of existing modules.

Modules can be written in any language and are found in the path specified
by :envvar:`ANSIBLE_LIBRARY` or the ``--module-path`` command line option.

By default, everything that ships with Ansible is pulled from its source tree, but
additional paths can be added.

The directory :file:`./library`, alongside your top level :term:`playbooks`, is also automatically
added as a search directory.

Should you develop an interesting Ansible module, consider sending a pull request to the
`modules-extras project <https://github.com/ansible/ansible-modules-extras>`_.  There's also a core
repo for more established and widely used modules.  "Extras" modules may be promoted to core periodically,
but there's no fundamental difference in the end - both ship with Ansible, all in one package, regardless
of how you acquire Ansible.

.. _module_dev_should_you:

Should You Develop A Module?
````````````````````````````
Before diving into the work of creating a new module, you should think about whether you actually *should* 
develop a module. Ask the following questions:

1. Does a similar module already exist? 

There are a lot of existing modules available, and more that are in development. You should check out the list of existing modules at :doc:`../modules` or look at the module PRs for the ansible repository and see if a module that does what you want exists or is in development.

2. Should you use or develop an action plugin instead? 

Action plugins get run on the master instead of on the target. For modules like file/copy/template, some of the work needs to be done on the master before the module executes on the target. Action plugins execute first on the master and can then execute the normal module on the target if necessary. 

For more information about action plugins, go here: (TODO: link here)

3. Should you use a role instead?

Check out the roles documentation `here <http://docs.ansible.com/ansible/playbooks_roles.html#roles>`_.  
 

.. _developing_modules_all:

How To Develop A Module
```````````````````````

The following topics will discuss how to develop modules:

:doc:`developing_modules_general`
    A general overview of how to develop, debug, and test modules
:doc:`../guide_aws`
    Working with Amazon Web Services (AWS) modules.
:doc:`developing_modules_python3`
    Adding Python 3 support to modules (all new modules must be py2.4 and py3 compatible).
:doc:`../guide_network_modules`
    Working with Network modules.
:doc:`i../ntro_windows`
    Working with Windows modules.


.. include:: ./developing_modules_documenting.rst

.. include:: ./developing_modules_best_practices.rst

.. include:: ./developing_module_contributing.rst

.. seealso::

   :doc:`../modules`
       Learn about available modules
   :doc:`developing_plugins`
       Learn about developing plugins
   :doc:`developing_api`
       Learn about the Python API for playbook and task execution
   `GitHub Core modules directory <https://github.com/ansible/ansible-modules-core/tree/devel>`_
       Browse source of core modules
   `Github Extras modules directory <https://github.com/ansible/ansible-modules-extras/tree/devel>`_
       Browse source of extras modules.
   `Mailing List <http://groups.google.com/group/ansible-devel>`_
       Development mailing list
   `irc.freenode.net <http://irc.freenode.net>`_
       #ansible IRC chat channel


.. include:: ./developing_module_utilities.rst
