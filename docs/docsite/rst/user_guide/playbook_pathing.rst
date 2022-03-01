:orphan:

***********************
Search paths in Ansible
***********************

You can control the paths Ansible searches to find resources on your control node (including configuration, modules, roles, ssh keys, and more) as well as resources on the remote nodes you are managing. Use absolute paths to tell Ansible where to find resources whenever you can. However, absolute paths are not always practical. This page covers how Ansible interprets relative search paths, along with ways to troubleshoot when Ansible cannot find the resource you need.

.. contents::
   :local:

Config paths
============

By default these should be relative to the config file, some are specifically relative to the current working directory or the playbook and should have this noted in their description. Things like ssh keys are left to use the current working directory because it mirrors how the underlying tools would use it.


Task paths
==========

Task paths include two different scopes: task evaluation and task execution. For task evaluation, all paths are local, like in lookups. For task execution, which usually happens on the remote nodes, local paths do not usually apply. However, if a task uses an action plugin, it uses a local path. The template and copy modules are examples of modules that use action plugins, and therefore use local paths.

The magic of 'local' paths
--------------------------

Lookups and action plugins both use a special 'search magic' to find things, taking the current play into account, it uses from most specific to most general playbook dir in which a task is contained (this includes roles and includes).

Using this magic, relative paths get attempted first with a 'files|templates|vars' appended (if not already present), depending on action being taken, 'files' is the default. (in other words, include_vars will use vars/).  The paths will be searched from most specific to most general (in other words, role before play).
dependent roles WILL be traversed (in other words, task is in role2, role2 is a dependency of role1, role2 will be looked at first, then role1, then play).
i.e :

.. code-block:: text

    role search path is rolename/{files|vars|templates}/, rolename/tasks/.
    play search path is playdir/{files|vars|templates}/, playdir/.


By default, Ansible does not search the current working directory unless it happens to coincide with one of the paths above. If you `include` a task file from a role, it  will NOT trigger role behavior, this only happens when running as a role, `include_role` will work. A new variable `ansible_search_path` var will have the search path used, in order (but without the appended subdirs). Using 5 "v"s (`-vvvvv`) should show the detail of the search as it happens.

As for includes, they try the path of the included file first and fall back to the play/role that includes them.



.. note::  The current working directory might vary depending on the connection plugin and if the action is local or remote. For the remote it is normally the directory on which the login shell puts the user. For local it is either the directory you executed ansible from or in some cases the playbook directory.
