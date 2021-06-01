Error Handling In Playbooks
===========================

.. contents:: Topics

Ansible normally has defaults that make sure to check the return codes of commands and modules and
it fails fast -- forcing an error to be dealt with unless you decide otherwise.

Sometimes a command that returns different than 0 isn't an error.  Sometimes a command might not always
need to report that it 'changed' the remote system.  This section describes how to change
the default behavior of Ansible for certain tasks so output and error handling behavior is
as desired.

.. _ignoring_failed_commands:

Ignoring Failed Commands
````````````````````````

Generally playbooks will stop executing any more steps on a host that has a task fail.
Sometimes, though, you want to continue on.  To do so, write a task that looks like this::

    - name: this will not be counted as a failure
      command: /bin/false
      ignore_errors: yes

Note that the above system only governs the return value of failure of the particular task,
so if you have an undefined variable used or a syntax error, it will still raise an error that users will need to address.
Note that this will not prevent failures on connection or execution issues.
This feature only works when the task must be able to run and return a value of 'failed'.

.. _resetting_unreachable:

Resetting Unreachable Hosts
```````````````````````````

.. versionadded:: 2.2

Connection failures set hosts as 'UNREACHABLE', which will remove them from the list of active hosts for the run.
To recover from these issues you can use `meta: clear_host_errors` to have all currently flagged hosts reactivated,
so subsequent tasks can try to use them again.


.. _handlers_and_failure:

Handlers and Failure
````````````````````

When a task fails on a host, handlers which were previously notified
will *not* be run on that host. This can lead to cases where an unrelated failure
can leave a host in an unexpected state. For example, a task could update
a configuration file and notify a handler to restart some service. If a
task later on in the same play fails, the service will not be restarted despite
the configuration change.

You can change this behavior with the ``--force-handlers`` command-line option,
or by including ``force_handlers: True`` in a play, or ``force_handlers = True``
in ansible.cfg. When handlers are forced, they will run when notified even
if a task fails on that host. (Note that certain errors could still prevent
the handler from running, such as a host becoming unreachable.)

.. _controlling_what_defines_failure:

Controlling What Defines Failure
````````````````````````````````

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

In previous version of Ansible, this can still be accomplished as follows::

    - name: this command prints FAILED when it fails
      command: /usr/bin/example-command -x -y -z
      register: command_result
      ignore_errors: True

    - name: fail the play if the previous command did not succeed
      fail:
        msg: "the command failed"
      when: "'FAILED' in command_result.stderr"

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

Overriding The Changed Result
`````````````````````````````

When a shell/command or other module runs it will typically report
"changed" status based on whether it thinks it affected machine state.

Sometimes you will know, based on the return code
or output that it did not make any changes, and wish to override
the "changed" result such that it does not appear in report output or
does not cause handlers to fire::

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

Aborting the play
`````````````````

Sometimes it's desirable to abort the entire play on failure, not just skip remaining tasks for a host.

The ``any_errors_fatal`` option will end the play and prevent any subsequent plays from running. When an error is encountered, all hosts in the current batch are given the opportunity to finish the fatal task and then the execution of the play stops. ``any_errors_fatal`` can be set at the play or block level::

     - hosts: somehosts
       any_errors_fatal: true
       roles:
         - myrole

     - hosts: somehosts
       tasks:
         - block:
             - include_tasks: mytasks.yml
           any_errors_fatal: true

for finer-grained control ``max_fail_percentage`` can be used to abort the run after a given percentage of hosts has failed.

Using blocks
````````````

Most of what you can apply to a single task (with the exception of loops) can be applied at the :ref:`playbooks_blocks` level, which also makes it much easier to set data or directives common to the tasks.
Blocks also introduce the ability to handle errors in a way similar to exceptions in most programming languages.
Blocks only deal with 'failed' status of a task. A bad task definition or an unreachable host are not 'rescuable' errors::

    tasks:
    - name: Handle the error
      block:
        - debug:
            msg: 'I execute normally'
        - name: i force a failure
          command: /bin/false
        - debug:
            msg: 'I never execute, due to the above task failing, :-('
      rescue:
        - debug:
            msg: 'I caught an error, can do stuff here to fix it, :-)'

This will 'revert' the failed status of the outer ``block`` task for the run and the play will continue as if it had succeeded.
See :ref:`block_error_handling` for more examples.

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
   `irc.libera.chat <https://libera.chat/>`_
       #ansible IRC chat channel
