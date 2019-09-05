.. _playbooks_reuse:

Creating Reusable Playbooks
===========================

.. toctree::
   :maxdepth: 1

   playbooks_reuse_includes
   playbooks_reuse_roles

While it is possible to write a playbook in one very large file (and you might start out learning playbooks this way), eventually you'll want to reuse files and start to organize things. In Ansible, there are three ways to do this: includes, imports, and roles.

Includes and imports (added in Ansible version 2.4) allow users to break up large playbooks into smaller files, which can be used across multiple parent playbooks or even multiple times within the same Playbook.

Roles allow more than just tasks to be packaged together and can include variables, handlers, or even modules and other plugins. Unlike includes and imports, roles can also be uploaded and shared via Ansible Galaxy.

.. _dynamic_vs_static:

Dynamic vs. Static
``````````````````

Ansible has two modes of operation for reusable content: dynamic and static.

In Ansible 2.0, the concept of *dynamic* includes was introduced. Due to some limitations with making all includes dynamic in this way, the ability to force includes to be *static* was introduced in Ansible 2.1. Because the *include* task became overloaded to encompass both static and dynamic syntaxes, and because the default behavior of an include could change based on other options set on the Task, Ansible 2.4 introduces the concept of ``include`` vs. ``import``.

If you use any ``include*`` Task (``include_tasks``, ``include_role``, etc.), it will be *dynamic*.
If you use any ``import*`` Task (``import_playbook``, ``import_tasks``, etc.), it will be *static*.

The bare ``include`` task (which was used for both Task files and Playbook-level includes) is still available, however it is now considered *deprecated*.

Differences Between Dynamic and Static
``````````````````````````````````````

The two modes of operation are pretty simple:

* Dynamic includes are processed during runtime at the point in which that task is encountered.
* Ansible pre-processes all static imports during Playbook parsing time.

When it comes to Ansible task options like ``tags`` and conditional statements (``when:``):

* For dynamic includes, the task options will *only* apply to the dynamic task as it is evaluated, and will not be copied to child tasks.
* For static imports, the parent task options will be copied to all child tasks contained within the import.

.. note::
    Roles are a somewhat special case. Prior to Ansible 2.3, roles were always statically included via the special ``roles:`` option for a given play and were always executed first before any other play tasks (unless ``pre_tasks`` were used). Roles can still be used this way, however, Ansible 2.3 introduced the ``include_role`` option to allow roles to be executed inline with other tasks.

Tradeoffs and Pitfalls Between Includes and Imports
```````````````````````````````````````````````````

Using ``include*`` vs. ``import*`` has some advantages as well as some tradeoffs which users should consider when choosing to use each:

The primary advantage of using ``include*`` statements is looping. When a loop is used with an include, the included tasks or role will be executed once for each item in the loop.

Using ``include*`` does have some limitations when compared to ``import*`` statements:

* Tags which only exist inside a dynamic include will not show up in ``--list-tags`` output.
* Tasks which only exist inside a dynamic include will not show up in ``--list-tasks`` output.
* You cannot use ``notify`` to trigger a handler name which comes from inside a dynamic include (see note below).
* You cannot use ``--start-at-task`` to begin execution at a task inside a dynamic include.

Using ``import*`` can also have some limitations when compared to dynamic includes:

* As noted above, loops cannot be used with imports at all.
* When using variables for the target file or role name, variables from inventory sources (host/group vars, etc.) cannot be used.
* Handlers using ``import*`` will not be triggered when notified by their name, as importing overwrites the handler's named task with the imported task list.

.. note::
    Regarding the use of ``notify`` for dynamic tasks: it is still possible to trigger the dynamic include itself, which would result in all tasks within the include being run.

.. seealso::

   :ref:`utilities_modules`
       Documentation of the ``include*`` and ``import*`` modules discussed here.
   :ref:`working_with_playbooks`
       Review the basic Playbook language features
   :ref:`playbooks_variables`
       All about variables in playbooks
   :ref:`playbooks_conditionals`
       Conditionals in playbooks
   :ref:`playbooks_loops`
       Loops in playbooks
   :ref:`playbooks_best_practices`
       Various tips about managing playbooks in the real world
   :ref:`ansible_galaxy`
       How to share roles on galaxy, role management
   `GitHub Ansible examples <https://github.com/ansible/ansible-examples>`_
       Complete playbook files from the GitHub project source
   `Mailing List <https://groups.google.com/group/ansible-project>`_
       Questions? Help? Ideas?  Stop by the list on Google Groups
