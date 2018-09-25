.. _special_variables:

Special Variables
=================

Magic
-----
These variables are directly not settable by the user, Ansible will always override them to reflect internal state.

ansible_check_mode
    Boolean that indicates if we are in check mode or not

ansible_diff_mode
    Boolean that indicates if we are in diff mode or not

ansible_forks
    Integer reflecting the number of maximum forks available to this run

ansible_inventory_sources
    List of sources used as inventory

ansible_play_batch
    List of active hosts in the current play run limited by the serial, aka 'batch'. Failed/Unreachable hosts are not considered 'active'.

ansible_play_hosts
    The same as ansible_play_batch

ansible_play_hosts_all
    List of all the hosts that were targeted by the play

ansible_playbook_python
    The path to the python interpreter being used by Ansible on the controller

ansible_serach_path
    Current search path for action plugins and lookups, i.e where we search for relative paths when you do ``template: src=myfile``

ansible_verbosity
    Current verbosity setting for Ansible

ansible_version
   Dictionary/map that contains information about the current running version of ansible, it has the following keys: full, major, minor, revision and string.

group_names
    List of groups the current host is part of

groups
    A dictionary/map with all the groups in inventory and each group has the list of hosts that belong to it

hostvars
    A dictionary/map with all the hosts in inventory and variables assigned to them

inventory_hostname
    The inventory name for the 'current' host being iterated over in the play

inventory_hostname_short
    The short version of `inventory_hostname`

inventory_dir
    The directory of the inventory source in which the `inventory_hostname` was first defined

inventory_file
    The file name of the inventory source in which the `inventory_hostname` was first defined

omit
    Special variable that allows you to 'omit' an option in a task, i.e ``- user: name=bob home={{ bobs_home|default(omit)}}``

play_hosts
    Deprecated, the same as ansbile_play_batch

playbook_dir
    The path to the directory of the playbook that was passed to the ``ansible-playbook`` command line.

role_names
    The names of the rules currently imported into the current play.

role_path
    The path to the dir of the currently running role

Facts
-----
These are variables that contain information pertinent to the current host (`inventory_hostname`), they are only available if gathered first.

ansible_facts
    Contains any facts gathered or cached for the `inventory_hostname`
    Facts are normally gathered by the M(setup) module automatically in a play, but any module can return facts.

ansible_local
    Contains any 'local facts' gathred or cached for the `inventory_hostname`.
    The keys available depend on the custom facts created.
    See the M(setup) module for more details.

Connection variables
---------------------
These are variables are normally used to set the specifics on how to execute actions on a target,
most of them correspond to connection plugins but not all are specific to them, other plugins like shell, terminal and become are normally involved.
Only the common ones are described as each connection/become/shell/etc plugin can define it's own overrides and specific variables.

ansible_become_user
    The user Ansible 'becomes' after using privilege escalation, this must be available to the 'login user'.

ansible_connecion
    The connection plugin actually used for the task on the target host.

ansible_host
    The ip/name of the target host to use instead of `inventory_hostname`.

ansible_python_interpreter
    The path to the Python executable Ansible should use on the target host.

ansible_user
    The user Ansible 'logs in' as.

