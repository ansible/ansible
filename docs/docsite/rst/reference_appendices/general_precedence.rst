.. _general_precedence_rules:

Controlling how Ansible behaves: precedence rules
=================================================

To give you maximum flexibility in managing your environments, Ansible supports many ways to control how Ansible behaves: how it connects to managed nodes, how it works once it has connected.
If you use Ansible to manage a large number of servers, network devices, and cloud resources, you may define Ansible behavior in several different places and pass that information to Ansible in several different ways.
This flexibility is convenient, but it can backfire if you do not understand the precedence rules.

These precedence rules apply to any setting that can be defined in multiple ways (by configuration settings, command-line options, playbook keywords, variables). For example, defining connection information, selecting a temporary directory, and choosing the correct python/ruby/powershell/etc interpreter to invoke for a module using settings like ANSIBLE_USER, DEFAULT_LOCAL_TMP, or ANSIBLE_PYTHON_INTERPRETER all follow these precedence rules.

.. contents::
   :local:

Precedence categories
---------------------

Ansible supports four sources for controlling its behavior. In order of precedence from lowest (most easily overridden) to highest (overrides all others), the categories are:

   Configuration settings
   Command-line options
   Playbook keywords
   Variables

Each category overrides any information from all lower-precedence categories. For example, a playbook keyword will override any configuration setting.

Within each precedence category, specific rules apply. However, generally speaking, 'last defined' wins and overrides any previous definitions.

Configuration settings
^^^^^^^^^^^^^^^^^^^^^^

:ref:`Configuration settings<ansible_configuration_settings>` include both values from the ``ansible.cfg`` file and environment variables. Within this category, values set in configuration files have lower precedence. Ansible uses the first ``ansible.cfg`` file it finds, looking in these locations in order:

   #. the file specified by the value of ``ANSIBLE_CONFIG``
   #. config in the current working directory: `./ansible.cfg`
   #. config in the current user's home directory: `~/.ansible.cfg`
   #. global config: `/etc/ansible/ansible.cfg`

Environment variables have a higher precedence than entries in ``ansible.cfg``. If you have environment variables set, they override the settings in whichever ``ansible.cfg`` file Ansible loads. The value of any given environment variable follows normal shell precedence: the last value defined overwrites previous values. (TODO: Does Ansible use the envvars defined on the control node or on the managed node?)

You can use the :ref:`ansible-config` command line utility to see the current value of a configuration item and where it came from. (TODO: How does this work? Add example.)

Command-line options
^^^^^^^^^^^^^^^^^^^^

Any command-line option will override any configuration setting.

At the command line, if you pass multiple values for a parameter that accepts only a single value, the last defined value wins. For example, this :ref:`ad-hoc task<intro_adhoc>` will connect as ``carol``, not as ``mike``::

      ansible -u mike -m ping myhost -u carol

Some parameters allow multiple values. In this case, Ansible will append all values from the hosts listed in inventory files inventory1 and inventory2::

   ansible -i /path/inventory1 -i /path/inventory2 -m ping all

The help for each :ref:`command-line tool<command_line_tools>` specifies which parameters allow for multiple entries.

Most command-line options deal with generic settings, but some settings are specific to connections and strategies.
Passing these options at the command-line may feel like the highest-precedence options, but command-line options have low precedence - they override configuration only. They do not override playbook keywords, variables from inventory or variables from playbooks.
You can override all other settings from all other sources in all other precedence categories at the command line with ``--extra-vars var_name=value``, but that is not a command-line option, it is a variable.

Playbook keywords
^^^^^^^^^^^^^^^^^

Any :ref:`playbook keyword<playbook_keywords>` will override any command-line option and any configuration setting.

Within playbook keywords, precedence is probably the simplest, as it flows with the playbook itself; the more specific wins against the more general:

- play (most general)
- blocks/includes/imports/roles (optional and can contain tasks and each other)
- tasks (most specific)

A simple example::

   - hosts: all
     connection: ssh
     tasks:
       - name: This task uses ssh.
         ping:

       - name: This task uses paramiko.
         connection: paramiko
         ping:

In this example, the ``connection`` keyword is set to ``ssh`` at the play level. The first task inherits that value, and connects using ``ssh``. The second task inherits that value, overrides it, and connects using ``paramiko``.
The same logic applies to blocks and roles as well. All tasks, blocks, and roles within a play inherit play-level keywords; any task, block, or role can override any play-level keyword by defining a different value for that keyword within the task, block, or role.

Remember that these are KEYWORDS, not variables. Both playbooks and variable files are defined in YAML but they have different significance.
Playbooks are the command or 'state description' structure for Ansible, variables are data we use to help make playbooks more dynamic.

Variables
^^^^^^^^^

Any variable will override any playbook keyword, any command-line option, and any configuration setting.

Variables can be set in multiple ways and places. You can define variables for hosts and groups in inventory. You can define variables for tasks and plays in ``vars:`` blocks in playbooks. However, they are still variables - they are data, not keywords or configuration settings. Variables that override playbook keywords and configuration settings follow the same rules of :ref:`variable precedence <ansible_variable_precedence>` as any other variables.

When setting variables in playbooks, remember that there are a couple of levels of scoping in playbooks. The first is 'playbook object scope'::

   - hosts: localhost
     gather_facts: false
     vars:
       me: play
     tasks:
       - name: the value is the play level one
         debug: var=me
       - block:
           - name: the block controls the value here
             debug: var=me
         vars:
           me: inblock
       - name: the task overrides the play level value
         debug: var=me
         vars:
           me: debugtask

       - name: we are back to the play scope value
         debug: var=me

These variables don't survive the playbook object they were defined in and will not be available to subsequent objects, including other plays.

And there is also a 'host scope' - variables that are directly associated with the host (also available via the `hostvars[]` dictionary). The host scope variables are  available across plays and are  defined in inventory, vars plugins, or from modules (set_fact, include_vars).

Using ``-e`` extra variables at the command line
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To override all other settings in all other categories, you can use extra variables: ``--extra-vars`` or ``-e`` at the command line. Values passed with ``-e`` are variables, not command-line options, and they will override command-line options as well as variables set elsewhere. For example this task will connect as ``brian`` not as ``carol``::

   ansible -u carol -e 'ansible_user=brian' -a whoami all

You must specify both the variable name and the value with ``--extra-vars``.
