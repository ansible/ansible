relative paths get attempted first with a 'files|templates|vars' in path (if not already present) depending on action being taken, 'files' is the default. (i.e include_vars will use vars/).
paths will be searched from most specific to most general (i.e role before play).
dependent roles WILL be traversed (i.e task is in role2, role2 is a dependency of role1, role2 will be looked at first, then role1, then play).
role search path is rolename/{files|vars|templates}/, rolename/tasks/.
play search path is playdir/{files|vars|templates}/, playdir/.
the current working directory (cwd) is not searched. If you see it, it just happens to coincide with one of the paths above.
include of a task file from a role will NOT trigger role behavior, this only happens when running as a role.
new ansible_search_path var will have the search path used, in order.
5 vs (-vvvvv) should show the detail of the search as it happens.
this does NOT affect absolute paths
includes try the path of the included file first and fall back to the play/role that includes them.
