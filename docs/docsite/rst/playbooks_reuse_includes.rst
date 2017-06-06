Including and Importing
=======================

.. contents:: Topics

Includes vs. Imports
````````````````````

As noted in :doc:`playbooks_reuse`, include and import statements are very similar, however the Ansible executor engine treats them very differently.

- All ``import*`` statements are pre-processed at the time playbooks are parsed.
- All ``include*`` statements are processed as they encountered during the execution of the playbook.

Please refer to  :doc:`playbooks_reuse` for documentation concerning the trade-offs one may encounter when using each type.

Importing Playbooks
```````````````````

It is possible to include playbooks inside a master playbook. For example::

    ---
    import_playbook: webservers.yml
    import_playbook: databases.yml

Each playbook listed will be run in the order they are listed.


Including and Importing Task Files
``````````````````````````````````

Use of included task lists is a great way to define a role that system is going to fulfill. A task include file simply contains a flat list of tasks::

    # common_tasks.yml
    ---
    - name: placeholder foo
      command: /bin/foo
    - name: placeholder bar
      command: /bin/bar

You can then use ``import_tasks`` or ``include_tasks`` to include this file in your main task list::

    tasks:
    - import_tasks: common_tasks.yml
    # or
    - include_tasks: common_tasks.yml

You can also pass variables into imports and includes::

    tasks:
    - import_tasks: wordpress.yml wp_user=timmy
    - import_tasks: wordpress.yml wp_user=alice
    - import_tasks: wordpress.yml wp_user=bob

Variables can also be passed to include files using an alternative syntax, which also supports structured variables like dictionaries and lists::

    tasks:
    - include_tasks: wordpress.yml
      vars:
        wp_user: timmy
        ssh_keys:
        - "{{ lookup('file', 'keys/one.pub') }}"
        - "{{ lookup('file', 'keys/two.pub') }}"

Using either syntax, variables passed in can then be used in the included files. These variables will only be available to tasks within the included file. See :doc:`variable_precedence` for more details on variable inheritance and precedence.

Task include statements can be used at arbitrary depth.

.. note::
    Static and dynamic can be mixed, however this is not recommended as it may lead to difficult-to-diagnose bugs in your playbooks.

Includes and imports can also be used in the ``handlers:`` section; for instance, if you want to define how to restart apache, you only have to do that once for all of your playbooks.  You might make a handlers.yml that looks like::

   # more_handlers.yml
   ---
   - name: restart apache
     service: name=apache state=restarted

And in your main playbook file::

   handlers:
   - include_tasks: more_handlers.yml
   # or
   - import_tasks: more_handlers.yml

.. note::
    Be sure to refer to the limitations/trade-offs for handlers noted in :doc:`playbooks_reuse`.

You can mix in includes along with your regular non-included tasks and handlers.

Including and Importing Roles
`````````````````````````````

Please refer to :doc:`playbooks_reuse_roles` for details on including and importing roles.

.. seealso::

   :doc:`YAMLSyntax`
       Learn about YAML syntax
   :doc:`playbooks`
       Review the basic Playbook language features
   :doc:`playbooks_best_practices`
       Various tips about managing playbooks in the real world
   :doc:`playbooks_variables`
       All about variables in playbooks
   :doc:`playbooks_conditionals`
       Conditionals in playbooks
   :doc:`playbooks_loops`
       Loops in playbooks
   :doc:`modules`
       Learn about available modules
   :doc:`dev_guide/developing_modules`
       Learn how to extend Ansible by writing your own modules
   `GitHub Ansible examples <https://github.com/ansible/ansible-examples>`_
       Complete playbook files from the GitHub project source
   `Mailing List <http://groups.google.com/group/ansible-project>`_
       Questions? Help? Ideas?  Stop by the list on Google Groups

