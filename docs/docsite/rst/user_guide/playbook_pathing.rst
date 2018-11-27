:orphan:

***********************
Search paths in Ansible
***********************

Absolute paths are not an issue as they always have a known start, but relative paths ... well, they are relative.

Config paths
============

By default these should be relative to the config file, some are specifically relative to the 'cwd' or the playbook and should have this noted in their description. Things like ssh keys are left to use 'cwd' because it mirrors how the underlying tools would use it.


Task paths
==========

Here things start getting complicated, there are 2 different scopes to consider, task evaluation (paths are all local, like in lookups) and task execution, which is normally on the remote, unless an action plugin is involved.

Some tasks that require 'local' resources use action plugins (template and copy are examples of these), in which case the path is also local.

The magic of 'local' paths
--------------------------

Lookups and action plugins both use a special 'search magic' to find things, taking the current play into account, it uses from most specific to most general playbook dir in which a task is contained (this includes roles and includes).

Using this magic, relative paths get attempted first with a 'files|templates|vars' appended (if not already present), depending on action being taken, 'files' is the default. (i.e include_vars will use vars/).  The paths will be searched from most specific to most general (i.e role before play).
dependent roles WILL be traversed (i.e task is in role2, role2 is a dependency of role1, role2 will be looked at first, then role1, then play).
i.e ::

    role search path is rolename/{files|vars|templates}/, rolename/tasks/.
    play search path is playdir/{files|vars|templates}/, playdir/.


The current working directory (cwd) is not searched. If you see it, it just happens to coincide with one of the paths above.
If you `include` a task file from a role, it  will NOT trigger role behavior, this only happens when running as a role, `include_role` will work.
A new variable `ansible_search_path` var will have the search path used, in order (but without the appended subdirs). Using 5 "v"s (`-vvvvv`) should show the detail of the search as it happens.

As for includes, they try the path of the included file first and fall back to the play/role that includes them.



.. note:  The 'cwd' might vary depending on the connection plugin and if the action is local or remote. For the remote it is normally the directory on which the login shell puts the user. For local it is either the directory you executed ansible from or in some cases the playbook directory.
