.. _playbooks_error_handling:

***************************
Error handling in playbooks
***************************

When Ansible receives a non-zero return code from a command or a failure from a module, by default it stops executing on that host and continues on other hosts. However, in some circumstances you may want different behavior. Sometimes a non-zero return code indicates success. Sometimes you want a failure on one host to stop execution on all hosts. Ansible provides tools and settings to handle these situations and help you get the behavior, output, and reporting you want.

.. contents::
   :local:

.. _ignoring_failed_commands:

Ignoring failed commands
========================

By default Ansible stops executing tasks on a host when a task fails on that host. You can use ``ignore_errors`` to continue on in spite of the failure::

    - name: this will not count as a failure
      command: /bin/false
      ignore_errors: yes

The ``ignore_errors`` directive only works when the task is able to run and returns a value of 'failed'. It will not make Ansible ignore undefined variable errors, connection failures, execution issues (for example, missing packages), or syntax errors.

Ignoring unreachable host errors
================================

.. versionadded:: 2.7

You may ignore task failure due to the host instance being 'UNREACHABLE' with the ``ignore_unreachable`` keyword.
Note that task errors are what's being ignored, not the unreachable host.

Here's an example explaining the behavior for an unreachable host at the task level::

    - name: this executes, fails, and the failure is ignored
      command: /bin/true
      ignore_unreachable: yes

    - name: this executes, fails, and ends the play for this host
      command: /bin/true

And at the playbook level::

    - hosts: all
      ignore_unreachable: yes
      tasks:
      - name: this executes, fails, and the failure is ignored
        command: /bin/true

      - name: this executes, fails, and ends the play for this host
        command: /bin/true
        ignore_unreachable: no

.. _resetting_unreachable:

Resetting unreachable hosts
===========================

If Ansible cannot connect to a host, it marks that host as 'UNREACHABLE' and removes it from the list of active hosts for the run. You can use `meta: clear_host_errors` to reactivate all hosts, so subsequent tasks can try to reach them again.


.. _handlers_and_failure:

Handlers and failure
====================

Ansible runs :ref:`handlers <handlers>` at the end of each play. If a task notifies a handler but
another task fails later in the play, by default the handler does *not* run on that host,
which may leave the host in an unexpected state. For example, a task could update
a configuration file and notify a handler to restart some service. If a
task later in the same play fails, the configuration file might be changed but
the service will not be restarted.

You can change this behavior with the ``--force-handlers`` command-line option,
by including ``force_handlers: True`` in a play, or by adding ``force_handlers = True``
to ansible.cfg. When handlers are forced, Ansible will run all notified handlers on
all hosts, even hosts with failed tasks. (Note that certain errors could still prevent
the handler from running, such as a host becoming unreachable.)

.. _controlling_what_defines_failure:

Defining failure
================

Ansible lets you define what "failure" means in each task using the ``failed_when`` conditional. As with all conditionals in Ansible, lists of multiple ``failed_when`` conditions are joined with an implicit ``and``, meaning the task only fails when *all* conditions are met. If you want to trigger a failure when any of the conditions is met, you must define the conditions in a string with an explicit ``or`` operator.

You may check for failure by searching for a word or phrase in the output of a command::

    - name: Fail task when the command error output prints FAILED
      command: /usr/bin/example-command -x -y -z
      register: command_result
      failed_when: "'FAILED' in command_result.stderr"

or based on the return code::

    - name: Fail task when both files are identical
      raw: diff foo/file1 bar/file2
      register: diff_cmd
      failed_when: diff_cmd.rc == 0 or diff_cmd.rc >= 2

You can also combine multiple conditions for failure. This task will fail if both conditions are true::

    - name: Check if a file exists in temp and fail task if it does
      command: ls /tmp/this_should_not_be_here
      register: result
      failed_when:
        - result.rc == 0
        - '"No such" not in result.stdout'

If you want the task to fail when only one condition is satisfied, change the ``failed_when`` definition to::

      failed_when: result.rc == 0 or "No such" not in result.stdout

If you have too many conditions to fit neatly into one line, you can split it into a multi-line yaml value with ``>``::

    - name: example of many failed_when conditions with OR
      shell: "./myBinary"
      register: ret
      failed_when: >
        ("No such file or directory" in ret.stdout) or
        (ret.stderr != '') or
        (ret.rc == 10)

.. _override_the_changed_result:

Defining "changed"
==================

Ansible lets you define when a particular task has "changed" a remote node using the ``changed_when`` conditional. This lets you determine, based on return codes or output, whether a change should be reported in Ansible statistics and whether a handler should be triggered or not. As with all conditionals in Ansible, lists of multiple ``changed_when`` conditions are joined with an implicit ``and``, meaning the task only reports a change when *all* conditions are met. If you want to report a change when any of the conditions is met, you must define the conditions in a string with an explicit ``or`` operator. For example::

    tasks:

      - shell: /usr/bin/billybass --mode="take me to the river"
        register: bass_result
        changed_when: "bass_result.rc != 2"

      # this will never report 'changed' status
      - shell: wall 'beep'
        changed_when: False

You can also combine multiple conditions to override "changed" result::

    - command: /bin/fake_command
      register: result
      ignore_errors: True
      changed_when:
        - '"ERROR" in result.stderr'
        - result.rc == 2

See :ref:`controlling_what_defines_failure` for more conditional syntax examples.

Ensuring success for command and shell
======================================

The :ref:`command <command_module>` and :ref:`shell <shell_module>` modules care about return codes, so if you have a command whose successful exit code is not zero, you may wish to do this::

    tasks:
      - name: run this command and ignore the result
        shell: /usr/bin/somecommand || /bin/true


Aborting a play on all hosts
============================

Sometimes you want a failure on a single host to abort the entire play on all hosts. If you set ``any_errors_fatal`` and a task returns an error, Ansible lets all hosts in the current batch finish the fatal task and then stops executing the play on all hosts. You can set ``any_errors_fatal`` at the play or block level::

     - hosts: somehosts
       any_errors_fatal: true
       roles:
         - myrole

     - hosts: somehosts
       tasks:
         - block:
             - include_tasks: mytasks.yml
           any_errors_fatal: true

For finer-grained control, you can use ``max_fail_percentage`` to abort the run after a given percentage of hosts has failed.

Controlling errors in blocks
============================

You can also use blocks to define responses to task errors. This approach is similar to exception handling in many programming languages. See :ref:`block_error_handling` for details and examples.

.. seealso::

   :ref:`playbooks_intro`
       An introduction to playbooks
   :ref:`playbooks_best_practices`
       Best practices in playbooks
   :ref:`playbooks_conditionals`
       Conditional statements in playbooks
   :ref:`playbooks_variables`
       All about variables
   `User Mailing List <https://groups.google.com/group/ansible-devel>`_
       Have a question?  Stop by the google group!
   `irc.freenode.net <http://irc.freenode.net>`_
       #ansible IRC chat channel
