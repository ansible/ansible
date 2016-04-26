Error Handling In Playbooks
===========================

.. contents:: Topics

Ansible normally has defaults that make sure to check the return codes of commands and modules and
it fails fast -- forcing an error to be dealt with unless you decide otherwise.

Sometimes a command that returns 0 isn't an error.  Sometimes a command might not always
need to report that it 'changed' the remote system.  This section describes how to change
the default behavior of Ansible for certain tasks so output and error handling behavior is
as desired.

.. _ignoring_failed_commands:

Ignoring Failed Commands
````````````````````````

.. versionadded:: 0.6

Generally playbooks will stop executing any more steps on a host that
has a failure.  Sometimes, though, you want to continue on.  To do so,
write a task that looks like this::

    - name: this will not be counted as a failure
      command: /bin/false
      ignore_errors: yes

Note that the above system only governs the return value of failure of the particular task,
so if you have an undefined variable used, it will still raise an error that users will need to address.
Neither will this prevent failures on connection nor execution issues, the task must be able to run and
return a value of 'failed'.


.. _handlers_and_failure:

Handlers and Failure
````````````````````

.. versionadded:: 1.9.1

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

.. versionadded:: 1.4

Suppose the error code of a command is meaningless and to tell if there
is a failure what really matters is the output of the command, for instance
if the string "FAILED" is in the output.  

Ansible in 1.4 and later provides a way to specify this behavior as follows::

    - name: this command prints FAILED when it fails
      command: /usr/bin/example-command -x -y -z
      register: command_result
      failed_when: "'FAILED' in command_result.stderr"

In previous version of Ansible, this can be still be accomplished as follows::

    - name: this command prints FAILED when it fails
      command: /usr/bin/example-command -x -y -z
      register: command_result
      ignore_errors: True

    - name: fail the play if the previous command did not succeed
      fail: msg="the command failed"
      when: "'FAILED' in command_result.stderr"

.. _override_the_changed_result:

Overriding The Changed Result
`````````````````````````````

.. versionadded:: 1.3

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

Aborting the play
`````````````````

Sometimes it's desirable to abort the entire play on failure, not just skip remaining tasks for a host.

The ``any_errors_fatal`` play option will mark all hosts as failed if any fails, causing an immediate abort::

     - hosts: somehosts
       any_errors_fatal: true
       roles:
         - myrole

for finer-grained control ``max_fail_percentage`` can be used to abort the run after a given percentage of hosts has failed.


.. seealso::

   :doc:`playbooks`
       An introduction to playbooks
   :doc:`playbooks_best_practices`
       Best practices in playbooks
   :doc:`playbooks_conditionals`
       Conditional statements in playbooks
   :doc:`playbooks_variables`
       All about variables
   `User Mailing List <http://groups.google.com/group/ansible-devel>`_
       Have a question?  Stop by the google group!
   `irc.freenode.net <http://irc.freenode.net>`_
       #ansible IRC chat channel


