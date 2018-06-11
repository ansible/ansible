Including and Importing
=======================

.. contents:: Topics

Includes vs. Imports
````````````````````

As noted in :doc:`playbooks_reuse`, include and import statements are very similar, however the Ansible executor engine treats them very differently.

- All ``import*`` statements are pre-processed at the time playbooks are parsed.
- All ``include*`` statements are processed as they encountered during the execution of the playbook.

Please refer to  :doc:`playbooks_reuse` for documentation concerning the trade-offs one may encounter when using each type.

Also be aware that this behaviour changed in 2.4. Prior to Ansible 2.4, only ``include`` was available and it behaved differently depending on context.

.. versionadded:: 2.4

Importing Playbooks
```````````````````

It is possible to include playbooks inside a master playbook. For example::

    - import_playbook: webservers.yml
    - import_playbook: databases.yml

The plays and tasks in each playbook listed will be run in the order they are listed, just as if they had been defined here directly.

Prior to 2.4 only ``include`` was available and worked for both playbooks and tasks as both import and include.


.. versionadded:: 2.4

Including and Importing Task Files
``````````````````````````````````

Breaking tasks up into different files is an excellent way to organize complex sets of tasks or reuse them. A task file simply contains a flat list of tasks::

    # common_tasks.yml
    - name: placeholder foo
      command: /bin/foo
    - name: placeholder bar
      command: /bin/bar

You can then use ``import_tasks`` or ``include_tasks`` to execute the tasks in a file in the main task list::

    tasks:
    - import_tasks: common_tasks.yml
    # or
    - include_tasks: common_tasks.yml

You can also pass variables into imports and includes::

    tasks:
    - import_tasks: wordpress.yml
      vars:
        wp_user: timmy
    - import_tasks: wordpress.yml
      vars:
        wp_user: alice
    - import_tasks: wordpress.yml
      vars:
        wp_user: bob

See :ref:`ansible_variable_precedence` for more details on variable inheritance and precedence.

Task include and import statements can be used at arbitrary depth.

.. note::
    - Static and dynamic can be mixed, however this is not recommended as it may lead to difficult-to-diagnose bugs in your playbooks.
    - The ``key=value`` syntax for passing variables to import and include is deprecated. Use YAML ``vars:`` instead.

Includes and imports can also be used in the ``handlers:`` section. For instance, if you want to define how to restart Apache, you only have to do that once for all of your playbooks. You might make a ``handlers.yml`` that looks like::

   # more_handlers.yml
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

   :ref:`yaml_syntax`
       Learn about YAML syntax
   :ref:`working_with_playbooks`
       Review the basic Playbook language features
   :ref:`playbooks_best_practices`
       Various tips about managing playbooks in the real world
   :ref:`playbooks_variables`
       All about variables in playbooks
   :ref:`playbooks_conditionals`
       Conditionals in playbooks
   :ref:`playbooks_loops`
       Loops in playbooks
   :ref:`all_modules`
       Learn about available modules
   :ref:`developing_modules`
       Learn how to extend Ansible by writing your own modules
   `GitHub Ansible examples <https://github.com/ansible/ansible-examples>`_
       Complete playbook files from the GitHub project source
   `Mailing List <http://groups.google.com/group/ansible-project>`_
       Questions? Help? Ideas?  Stop by the list on Google Groups

