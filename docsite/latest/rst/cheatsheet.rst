Ansible Cheatsheet
==================

An attempt to list out all valid Ansible playbook, tasks, conditional parameters.

.. contents::
  :depth: 2
  :backlinks: top

Playbook Attributes
+++++++++++++++++++

========================== ======= ========
Playbook Attributes          1.1     1.2
========================== ======= ========
`any_errors_fatal`_
`connection`_
`gather_facts`_ 
`handlers`_ 
`hosts`_ 
`include`_ 
`name`_ 
`port`_ 
`post_tasks`_ 
`pre_tasks`_ 
`roles`_ 
`serial`_ 
`sudo`_ 
`sudo_user`_ 
`tags`_ 
`tasks`_ 
`user`_ 
`vars`_ 
`vars_files`_ 
`vars_prompt`_ 
========================== ======= ========


Conditional operators
+++++++++++++++++++++

========================== ======= ========
Conditionals                 1.1     1.2
========================== ======= ========
`when_failed`_ 
`when_changed`_ 
`when_string`_ 
`when_boolean`_ 
`when_bool`_ 
`when_integer`_ 
`when_float`_ 
`when_set`_ 
`when_unset`_ 
`jinja2_compare`_ 
`only_if`_ 
========================== ======= ========

Lookup plugins
++++++++++++++
=========================== ======= ========
Lookups                     1.1      1.2
=========================== ======= ========
`with_items`_ 
`with_sequence`_ 
`with_fileglob`_ 
`with_file`_ 
`with_first_found`_ 
`with_inventory_hostnames`_ 
`with_random_choice`_ 
`with_lines`_ 
`with_pipe`_ 
`with_env`_ 
`with_dnstxt`_ 
`with_template`_ 
`with_redis_kv`_ 
`with_password`_ 
`with_nested`_ 
`first_available_file`_ 
=========================== ======= ========

.. _any_errors_fatal: #any_errors_fatal
.. _connection: #connection
.. _gather_facts: #gather_facts
.. _handlers: #handlers
.. _hosts: #hosts
.. _include: #include
.. _name: #name
.. _port: #port
.. _post_tasks: #post_tasks
.. _pre_tasks: #pre_tasks
.. _roles: #roles
.. _serial: #serial
.. _sudo: #sudo
.. _sudo_user: #sudo_user
.. _tags: #tags
.. _tasks: #tasks
.. _user: #user
.. _vars: #vars
.. _vars_files: #vars_files
.. _vars_prompt: #vars_prompt


.. _when_failed: #when_failed
.. _when_changed: #when_changed
.. _when_string: #when_string
.. _when_boolean: #when_boolean
.. _when_bool: #when_bool
.. _when_integer: #when_integer
.. _when_float: #when_float
.. _when_set: #when_set
.. _when_unset: #when_unset
.. _jinja2_compare: #jinja2_compare
.. _only_if: #only_if


.. _with_items: #with_items
.. _with_sequence: #with_sequence
.. _with_fileglob: #with_fileglob
.. _with_file: #with_file
.. _with_first_found: #with_first_found
.. _with_inventory_hostnames: #with_inventory_hostnames
.. _with_random_choice: #with_random_choice
.. _with_lines: #with_lines
.. _with_pipe: #with_pipe
.. _with_env: #with_env
.. _with_dnstxt: #with_dnstxt
.. _with_template: #with_template
.. _with_redis_kv: #with_redis_kv
.. _with_password: #with_password
.. _with_nested: #with_nested
.. _first_available_file: #first_available_file

