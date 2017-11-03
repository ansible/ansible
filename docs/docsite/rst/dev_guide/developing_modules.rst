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
exiting.  They take arguments in one of several ways which we'll go into
as we work through this tutorial.

See :doc:`../modules` for a list of existing modules.

Modules can be written in any language and are found in the path specified
by :envvar:`ANSIBLE_LIBRARY` or the ``--module-path`` command line option or
in the `library section of the Ansible configuration file <http://docs.ansible.com/ansible/intro_configuration.html#library>`_.

.. _module_dev_should_you:

Should You Develop A Module?
````````````````````````````
Before diving into the work of creating a new module, you should think about whether you actually *should*
develop a module. Ask the following questions:

1. Does a similar module already exist?

There are a lot of existing modules available, you should check out the list of existing modules at :doc:`../modules`

2. Has someone already worked on a similar Pull Request?

It's possible that someone has already started developing a similar PR. There are a few ways to find open module Pull Requests:

* `GitHub new module PRs <https://github.com/ansible/ansible/labels/new_module>`_
* `All updates to modules <https://github.com/ansible/ansible/labels/module>`_
* `New module PRs listed by directory <https://ansible.sivel.net/pr/byfile.html>`_ search for `lib/ansible/modules/`

If you find an existing PR that looks like it addresses the issue you are trying to solve, please provide feedback on the PR -  this will speed up getting the PR merged.

3. Should you use or develop an action plugin instead?

Action plugins get run on the master instead of on the target. For modules like file/copy/template, some of the work needs to be done on the master before the module executes on the target. Action plugins execute first on the master and can then execute the normal module on the target if necessary.

For more information about action plugins, `read the action plugins documentation here <https://docs.ansible.com/ansible/dev_guide/developing_plugins.html>`_.

4. Should you use a role instead?

Check out the roles documentation `available here <http://docs.ansible.com/ansible/playbooks_reuse_roles.html#roles>`_.


.. _developing_modules_all:

How To Develop A Module
```````````````````````

The following topics will discuss how to develop and work with modules:

:doc:`developing_modules_general`
    A general overview of how to develop, debug, and test modules.
:doc:`developing_modules_general_windows`
    A general overview of how to develop, debug and test Windows modules.
:doc:`developing_modules_documenting`
    How to include in-line documentation in your module.
:doc:`developing_modules_best_practices`
    Best practices, recommendations, and things to avoid.
:doc:`developing_modules_checklist`
     Checklist for contributing your module to Ansible.
:doc:`testing`
    Developing unit and integration tests.
:doc:`developing_python3`
    Adding Python 3 support to modules (all new modules must be Python-2.6 and Python-3.5 compatible).
:doc:`developing_modules_in_groups`
    A guide for partners wanting to submit multiple modules.


.. seealso::

   :doc:`../modules`
       Learn about available modules
   :doc:`developing_plugins`
       Learn about developing plugins
   :doc:`developing_api`
       Learn about the Python API for playbook and task execution
   `GitHub modules directory <https://github.com/ansible/ansible/tree/devel/lib/ansible/modules>`_
       Browse module source code
   `Mailing List <http://groups.google.com/group/ansible-devel>`_
       Development mailing list
   `irc.freenode.net <http://irc.freenode.net>`_
       #ansible IRC chat channel


.. include:: ./developing_module_utilities.rst
