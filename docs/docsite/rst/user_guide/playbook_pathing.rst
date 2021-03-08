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

Relative paths used in a task typically refer to remote files and directories on the managed nodes. However, paths passed to lookup plugins and some paths used in action plugins such as the "src" path for the :ref:`template <ansible_collections.ansible.builtin.template_module>` and :ref:`copy <ansible_collections.ansible.builtin.copy_module>` modules refer to local files and directories on the control node.

Resolving local paths
---------------------

Ansible tries to find local files first in the current task's role, then in other roles that included or depend on the current role, and finally in the current play. This way, if multiple files with the same filename exist, Ansible will find the file that is closest to the current task and that is most likely to be file you wanted.

Specifically, Ansible searches these locations:

1. In the active role's matching "files", "vars", "templates", or "tasks" subdirectory, depending on which kind of file it is searching for.
2. In a previous role's matching subdirectory, if that role called into this current role with an `include_role` or `import_role` task or with a role dependency.
3. In the active play's matching subdirectory as well as directly in the active play's directory.

Ansible does not search the current working directory. (The directory you're in when you execute Ansible.) Also, Ansible will only search within a role if you actually included it with an `include_role` or `import_role` task or a dependency. If you use `include`, `include_task` or `import_task` to include just the tasks from a specific file but not the full role, Ansible will not try to search that role.

When you execute Ansible, the variable `ansible_search_path` will contain the paths searched, in the order they were searched in but without listing their subdirectories. If you run Ansible in verbosity level 5 by passing the `-vvvvv` argument, Ansible will report each directory while it searches.


.. note::  The current working directory might vary depending on the connection plugin and if the action is local or remote. For the remote it is normally the directory on which the login shell puts the user. For local it is either the directory you executed ansible from or in some cases the playbook directory.
