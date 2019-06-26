.. _playbook_debugger:

Playbook Debugger
=================

.. contents:: Topics

Ansible includes a debugger as part of the strategy plugins. This debugger enables you to debug as task.
You have access to all of the features of the debugger in the context of the task.  You can then, for example, check or set the value of variables, update module arguments, and re-run the task with the new variables and arguments to help resolve the cause of the failure.

There are multiple ways to invoke the debugger.

Using the debugger keyword
++++++++++++++++++++++++++

.. versionadded:: 2.5

The ``debugger`` keyword can be used on any block where you provide a ``name`` attribute, such as a play, role, block or task.

The ``debugger`` keyword accepts several values:

always
  Always invoke the debugger, regardless of the outcome

never
  Never invoke the debugger, regardless of the outcome

on_failed
  Only invoke the debugger if a task fails

on_unreachable
  Only invoke the debugger if the a host was unreachable

on_skipped
  Only invoke the debugger if the task is skipped

These options override any global configuration to enable or disable the debugger.

On a task
`````````

::

    - name: Execute a command
      command: false
      debugger: on_failed

On a play
`````````

::

    - name: Play
      hosts: all
      debugger: on_skipped
      tasks:
        - name: Execute a command
          command: true
          when: False

When provided at a generic level and a more specific level, the more specific wins::

    - name: Play
      hosts: all
      debugger: never
      tasks:
        - name: Execute a command
          command: false
          debugger: on_failed


Configuration or environment variable
+++++++++++++++++++++++++++++++++++++

.. versionadded:: 2.5

In ansible.cfg::

    [defaults]
    enable_task_debugger = True

As an environment variable::

    ANSIBLE_ENABLE_TASK_DEBUGGER=True ansible-playbook -i hosts site.yml

When using this method, any failed or unreachable task will invoke the debugger,
unless otherwise explicitly disabled.

As a Strategy
+++++++++++++

.. note::
     This is a backwards compatible method, to match Ansible versions before 2.5,
     and may be removed in a future release

To use the ``debug`` strategy, change the ``strategy`` attribute like this::

    - hosts: test
      strategy: debug
      tasks:
      ...

If you don't want change the code, you can define ``ANSIBLE_STRATEGY=debug``
environment variable in order to enable the debugger, or modify ``ansible.cfg`` such as::

    [defaults]
    strategy = debug


Examples
++++++++

For example, run the playbook below::

    - hosts: test
      debugger: on_failed
      gather_facts: no
      vars:
        var1: value1
      tasks:
        - name: wrong variable
          ping: data={{ wrong_var }}

The debugger is invoked since the *wrong_var* variable is undefined.

Let's change the module's arguments and run the task again

.. code-block:: none

    PLAY ***************************************************************************

    TASK [wrong variable] **********************************************************
    fatal: [192.0.2.10]: FAILED! => {"failed": true, "msg": "ERROR! 'wrong_var' is undefined"}
    Debugger invoked
    [192.0.2.10] TASK: wrong variable (debug)> p result._result
    {'failed': True,
     'msg': 'The task includes an option with an undefined variable. The error '
            "was: 'wrong_var' is undefined\n"
            '\n'
            'The error appears to have been in '
            "'playbooks/debugger.yml': line 7, "
            'column 7, but may\n'
            'be elsewhere in the file depending on the exact syntax problem.\n'
            '\n'
            'The offending line appears to be:\n'
            '\n'
            '  tasks:\n'
            '    - name: wrong variable\n'
            '      ^ here\n'}
    [192.0.2.10] TASK: wrong variable (debug)> p task.args
    {u'data': u'{{ wrong_var }}'}
    [192.0.2.10] TASK: wrong variable (debug)> task.args['data'] = '{{ var1 }}'
    [192.0.2.10] TASK: wrong variable (debug)> p task.args
    {u'data': '{{ var1 }}'}
    [192.0.2.10] TASK: wrong variable (debug)> redo
    ok: [192.0.2.10]

    PLAY RECAP *********************************************************************
    192.0.2.10               : ok=1    changed=0    unreachable=0    failed=0

This time, the task runs successfully!

.. _available_commands:

Available Commands
++++++++++++++++++

.. _pprint_command:

p(print) *task/task_vars/host/result*
`````````````````````````````````````

Print values used to execute a module::

    [192.0.2.10] TASK: install package (debug)> p task
    TASK: install package
    [192.0.2.10] TASK: install package (debug)> p task.args
    {u'name': u'{{ pkg_name }}'}
    [192.0.2.10] TASK: install package (debug)> p task_vars
    {u'ansible_all_ipv4_addresses': [u'192.0.2.10'],
     u'ansible_architecture': u'x86_64',
     ...
    }
    [192.0.2.10] TASK: install package (debug)> p task_vars['pkg_name']
    u'bash'
    [192.0.2.10] TASK: install package (debug)> p host
    192.0.2.10
    [192.0.2.10] TASK: install package (debug)> p result._result
    {'_ansible_no_log': False,
     'changed': False,
     u'failed': True,
     ...
     u'msg': u"No package matching 'not_exist' is available"}

.. _update_args_command:

task.args[*key*] = *value*
``````````````````````````

Update module's argument.

If you run a playbook like this::

    - hosts: test
      strategy: debug
      gather_facts: yes
      vars:
        pkg_name: not_exist
      tasks:
        - name: install package
          apt: name={{ pkg_name }}

Debugger is invoked due to wrong package name, so let's fix the module's args::

    [192.0.2.10] TASK: install package (debug)> p task.args
    {u'name': u'{{ pkg_name }}'}
    [192.0.2.10] TASK: install package (debug)> task.args['name'] = 'bash'
    [192.0.2.10] TASK: install package (debug)> p task.args
    {u'name': 'bash'}
    [192.0.2.10] TASK: install package (debug)> redo

Then the task runs again with new args.

.. _update_vars_command:

task_vars[*key*] = *value*
``````````````````````````

Update ``task_vars``.

Let's use the same playbook above, but fix ``task_vars`` instead of args::

    [192.0.2.10] TASK: install package (debug)> p task_vars['pkg_name']
    u'not_exist'
    [192.0.2.10] TASK: install package (debug)> task_vars['pkg_name'] = 'bash'
    [192.0.2.10] TASK: install package (debug)> p task_vars['pkg_name']
    'bash'
    [192.0.2.10] TASK: install package (debug)> update_task
    [192.0.2.10] TASK: install package (debug)> redo

Then the task runs again with new ``task_vars``.

.. note::
    In 2.5 this was updated from ``vars`` to ``task_vars`` to not conflict with the ``vars()`` python function.

.. _update_task_command:

u(pdate_task)
`````````````

.. versionadded:: 2.8

This command re-creates the task from the original task data structure, and templates with updated ``task_vars``

See the above documentation for :ref:`update_vars_command` for an example of use.

.. _redo_command:

r(edo)
``````

Run the task again.

.. _continue_command:

c(ontinue)
``````````

Just continue.

.. _quit_command:

q(uit)
``````

Quit from the debugger. The playbook execution is aborted.

Use with the free strategy
++++++++++++++++++++++++++

Using the debugger on the ``free`` strategy will cause no further tasks to be queued or executed
while the debugger is active. Additionally, using ``redo`` on a task to schedule it for re-execution
may cause the rescheduled task to execute after subsequent tasks listed in your playbook.


.. seealso::

   :ref:`playbooks_intro`
       An introduction to playbooks
   `User Mailing List <https://groups.google.com/group/ansible-devel>`_
       Have a question?  Stop by the google group!
   `irc.freenode.net <http://irc.freenode.net>`_
       #ansible IRC chat channel
