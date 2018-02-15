Network Getting Started: Beyond the Basics
======================================================

This page introduces some best practices for managing your Ansible files, along with intermediate concepts like roles, global configuration, privilege escalation, filters and conditional comparisons. Most of these concepts are common to all uses of Ansible, but there are differences in privilege escalation and conditional comparisons for network modules.

Beyond Playbooks: Moving Tasks and Variables into Roles
```````````````````````````````````````````````````````````````

Roles are sets of Ansible defaults, files, tasks, templates, variables, and other Ansible components that work together. Moving from a command to a playbook makes it easy to run multiple tasks and repeat the same tasks in the same order. Moving from a playbook to a role makes it even easier to reuse and share your ordered tasks. You call a role from a playbook with two lines:

.. code_block:: YAML

   Roles:
     - my_role_name

Ansible Galaxy lets you share your roles and use others' roles, either directly or as inspiration.

A Typical Ansible Filetree
```````````````````````````````````````````````````````````````

Ansible expects to find certain files in certain places. As you expand your inventory and create and run more network playbooks, keep your files organized in your working Ansible project directory like this:

.. code-block:: console

   .
   ├── backup
   │   ├── vyos.example.net_config.2018-02-08@11:10:15
   │   ├── vyos.example.net_config.2018-02-12@08:22:41
   ├── first_playbook.yml
   ├── inventory
   ├── group_vars
   │   ├── vyos.yml
   │   └── eos.yml
   ├── roles
   │   ├── static_route
   │   └── system
   ├── second_playbook.yml
   └── third_playbook.yml

The ``backup`` directory and the files in it get created when you run modules like ``vyos_config`` with the ``backup: yes`` parameter.


Tracking Changes to Inventory and Playbooks with Git
```````````````````````````````````````````````````````````````

To keep track of your inventory and playbooks, view history, track changes, and roll back mistakes, you must put your Ansible project under source control. We recommend Git as a source control solution. There are lots of good tutorials and guides to using Git out on the web.


Ansible Configuration: Setting global defaults
```````````````````````````````````````````````````````````````

Privilege Escalation: `authorize` and `become`
```````````````````````````````````````````````````````````````

Jinja2: Using Data with Filters and Tests
```````````````````````````````````````````````````````````````

Conditional Comparison in Network Modules
```````````````````````````````````````````````````````````````

Conditional statements in Ansible evaluate the output from a managed node to determine what happens next in a playbook. Linux/Unix and Windows modules use mathematical symbols (for example, `==`, `<`, and `>`) for comparison. However, network modules use different conditional comparisons. The conditional tests for network modules are:

- eq - Equal
- neq - Not equal
- gt - Greater than
- ge - Greater than or equal
- lt - Less than
- le - Less than or equal
- contains - Object contains specified item
