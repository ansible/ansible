.. _networking_working_with_command_output:

**********************************************
Working with Command Output in Network Modules
**********************************************

Conditionals in Networking Modules
===================================

Ansible allows you to use conditionals to control the flow of your playbooks. Ansible networking command modules use the following unique conditional statements.

* ``eq`` - Equal
* ``neq`` - Not equal
* ``gt`` - Greater than
* ``ge`` - Greater than or equal
* ``lt`` - Less than
* ``le`` - Less than or equal
* ``contains`` - Object contains specified item


Conditional statements evaluate the results from the commands that are
executed remotely on the device.  Once the task executes the command
set, the ``wait_for`` argument can be used to evaluate the results before
returning control to the Ansible playbook.

For example::

    ---
    - name: wait for interface to be admin enabled
      eos_command:
          commands:
              - show interface Ethernet4 | json
          wait_for:
              - "result[0].interfaces.Ethernet4.interfaceStatus eq connected"

In the above example task, the command :code:`show interface Ethernet4 | json`
is executed on the remote device and the results are evaluated.  If
the path
:code:`(result[0].interfaces.Ethernet4.interfaceStatus)` is not equal to
"connected", then the command is retried.  This process continues
until either the condition is satisfied or the number of retries has
expired (by default, this is 10 retries at 1 second intervals).

The commands module can also evaluate more than one set of command
results in an interface.  For instance::

    ---
    - name: wait for interfaces to be admin enabled
      eos_command:
          commands:
              - show interface Ethernet4 | json
              - show interface Ethernet5 | json
          wait_for:
              - "result[0].interfaces.Ethernet4.interfaceStatus eq connected"
              - "result[1].interfaces.Ethernet4.interfaceStatus eq connected"

In the above example, two commands are executed on the
remote device, and the results are evaluated.  By specifying the result
index value (0 or 1), the correct result output is checked against the
conditional.

The ``wait_for`` argument must always start with result and then the
command index in ``[]``, where ``0`` is the first command in the commands list,
``1`` is the second command, ``2`` is the third and so on.

