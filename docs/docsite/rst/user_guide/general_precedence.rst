.. contents:: Topics


How Ansible resolves configuration, data and keywords
=====================================================

Ansible has many ways to specify certain information, specially when dealing with 'connections'
as this information can be very sensitive to different factors and users have many different contexts to
deal with.

This desgin allows Ansible to deal with heterogeneous environments, i.e when a host or group of hosts will have different 'connection' information than the others and should always be accessed in this way.
You are not mandated to use the variables, but most people do out of convenience and then can get confused by their 'high precedence' and how to override them.

In general the precedence is simple, when things are defined at the same level, 'last wins', as per the levels
this is the most general list, from least to most:

 Configuration
 Command Line options
 Playbooks
 Connection variables

Some of these entries are not self evident and others also have their own internal levels and precedence, see them expanded below.


.. _what_is_configuration:

Configuration
`````````````

This mainly reffers to 2 things, 'the ansible configuration file' and environment variables. The internal precedence is as follows (from least to most):

   configuration file (only first found used, they don't merge)
      "value of ANSIBLE_CONFIG"
      `./ansible.cfg`
      `~/.ansible.cfg`
      `/etc/ansible/ansible.cfg`

   environment variable (this just follows normal shell precedence, last time defined overwrites previous values)

You can use the ``ansible-config`` command line utility to see the current value of a configuration item and where it came from.


.. _command_line_options_precedence:

Command line options
`````````````````````

The internal precedence is simple, but depends on the parameter used, 'last defined' wins (connects as carol, not mike)::

      ansible -u mike -m ping myhost -u carol

Unless the parameter allows for multiple entries and then they get appended (hosts are from inventory1 + inventory2)::

   ansible -i /path/inventory1 -i /path/inventory2 -m ping all

The help for each tool specifies which parameters allow for multiple entries.

Most of these options are supposed to deal with generic settings, but over time some very connection and strategy specific ones were added, they are also the main source of confusion as most of them have low precedence,
they are mostly meant to override configuration (which does NOT include playboks, inventory nor variables).

The one exception is 'extra vars' which sets variables with the highest precedence .. and since 'conneciton variables' are also the highest precedence it creates a short circut to it's own options::

   ansible -u myuser -e 'ansible_user=notmyuser' -a whoami all

This is the main source of confusion for people using Ansible, the above statement makes a redundant use of `-u` since it will be overriden by `ansible_user`. There is a reason for this and it has mostly to do with
how varied different installations are, `-u` makes sense when you don't use ``ansible_user`` anywhere, it allows you to override the 'current user' or configuration entries, but once you start using variables, you need
to keep in mind that they have high precedence making these options less useful in your context.


.. _playbook_precedence:

Playbook keywords
`````````````````
This is probably the simplest one as it flows with the playbook itself, the more specific wins against the more general:

   play (most general)
   blocks/includes/imports/roles (optional and can contain tasks and each other)
   tasks (most specific)

A simple example::

   - hosts: all
     connection: ssh
     tasks:
       - name: uses ssh
         ping:

       - name: test paramiko
         connection: paramiko
         ping:

The connection keyword is set at play level, all objects inside the play inherit it, but can also override it, the example above shows us doing so in a task, but a block/role will also work,
anything that can be contained in a play and that contains tasks itself is in the inheritance path.

Just to note these are KEYWORDS, not variables, both playbooks and variable files are defined in YAML but they have different significance.
Playbooks are the command or 'state description' strucutre for Ansible, variables are data we use to help make the playbooks more dynamic.


.. _connection_variables_flexible_confusion:

Connection Variables
````````````````````

Connection variables are 'normal variables' with specific names we have set as overrides for specific play keywords and configuration entries.
They are still just variables, data, not keywords nor configuration items. These variables are used to override host/group specific information needed to execute the actions.
Originally this was just 'connection parameters' but has been expanded to things like selecting the correct temporary directory to use and the correct python/ruby/powershell/etc interpreter to invoke for a module.

In the end they are just variables and follow normal variable precedence, which we already list here: https://docs.ansible.com/ansible/latest/user_guide/playbooks_variables.html#variable-precedence-where-should-i-put-a-variable
