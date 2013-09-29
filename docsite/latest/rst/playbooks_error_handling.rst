Error Handling
==============

Sometimes a command that returns 0 isn't an error.  Sometimes a command might not always
need to report that it 'changed' the remote system.  This section describes how to change
the default behavior of Ansible for certain tasks so output and error handling behavior is
as desired.

Ignoring Failed Commands
````````````````````````

.. versionadded:: 0.6

Generally playbooks will stop executing any more steps on a host that
has a failure.  Sometimes, though, you want to continue on.  To do so,
write a task that looks like this::

    - name: this will not be counted as a failure
      command: /bin/false
      ignore_errors: yes

Creates and Removes
```````````````````

The creates= and removes= flag on commands can say a command does not need to be run again
when a file exists (or does not exist).  This can bring "idempotence" to commands that
normally might produce errors when run a second time unneccessarily, or to avoid redundant
command execution.

    - name: install the foo
      command: /usr/bin/install-the-foo.sh creates=/opt/foo
      
In the above example, when /opt/foo exists, the command would not be executed.  See the
documentation for the command module in `modules` for more information.

Overriding Changed Result
`````````````````````````

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



