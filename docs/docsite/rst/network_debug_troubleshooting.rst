.. _network_debug_troubleshooting:

***************************************
Network Debug and Troubleshooting Guide
***************************************

.. contents:: Topics

Introduction
============

Starting with Ansible version 2.1, you can now use the familiar Ansible models of playbook authoring and module development to manage heterogeneous networking devices. Ansible supports a growing number of network devices using both CLI over SSH and API (when available) transports.

This section discusses how to debug and troubleshoot network modules in Ansible 2.3.





How to troubleshoot
===================

This section covers troubleshooting issues with Network Modules.

Errors generally fall into one of the following categories:

:Authentication issues:
  * Not correctly specifying credentials
  * Remote device (network switch/router) not falling back to other other authentication methods
  * SSH key issues
  * Use of ``delgate_to``, use ``ProxyCommand`` instead
:Timeout issues:
  * Can occur when trying to pull a large amount of data
  * May actually be masking a authentication issue
:Playbook issues:
  * Use of ``delgate_to``, instead of ``ProxyCommand``
  * Not using ``connection: local``



Enabling Networking logging and how to read the logfile
-------------------------------------------------------

**Platforms:** Any

Ansible 2.3 features improved logging to help diagnose and troubleshoot issues regarding Ansible Networking modules.

Because logging is very verbose it is disabled by default. It can be enabled via the ``ANSIBLE_LOG_PATH`` and ``ANISBLE_DEBUG`` options::

   # Specify the location for the log file
   export ANSIBLE_LOG_PATH=~/ansible.log

   # Run with 4*v for connection level verbosity
   ANSIBLE_DEBUG=True ansible-playbook -vvvv ...

After Ansible has finished running you can inspect the log file:

.. code::

  2017-03-30 13:19:52,740 p=28990 u=fred |  creating new control socket for host veos01:22 as user admin
  2017-03-30 13:19:52,741 p=28990 u=fred |  control socket path is /home/fred/.ansible/pc/ca5960d27a
  2017-03-30 13:19:52,741 p=28990 u=fred |  current working directory is /home/fred/ansible/test/integration
  2017-03-30 13:19:52,741 p=28990 u=fred |  using connection plugin network_cli
  ...
  2017-03-30 13:20:14,771 paramiko.transport userauth is OK
  2017-03-30 13:20:15,283 paramiko.transport Authentication (keyboard-interactive) successful!
  2017-03-30 13:20:15,302 p=28990 u=fred |  ssh connection done, setting terminal
  2017-03-30 13:20:15,321 p=28990 u=fred |  ssh connection has completed successfully
  2017-03-30 13:20:15,322 p=28990 u=fred |  connection established to veos01 in 0:00:22.580626


From the log notice:

* ``p=28990`` Is the PID (Process ID) of the ``ansible-connection`` process
* ``u=fred`` Is the user `running` ansible, not the remote-user you are attempting to connect as
* ``creating new control socket for host veos01:22 as user admin`` host:port as user
* ``control socket path is`` location on disk where the persistent connection socket is created
* ``using connection plugin network_cli`` Informs you that persistent connection is being used
* ``connection established to veos01 in 0:00:22.580626`` Time taken to obtain a shell on the remote device

Because the log files are verbose, you can use grep to look for specific information. For example, once you have identified the ```pid`` from the ``creating new control socket for host`` line you can search for other connection log entries::

  grep "p=28990" $ANSIBLE_LOG_PATH

Isolating an error
------------------

**Platforms:** Any

As with any effort to troubleshoot it's important to simplify the test case as much as possible.

For Ansible this can be done ensuring you are only running against one remote device:

* Using ``ansible-playbook --limit switch1.example.net...``
* Using an ad-hoc ``ansible`` command

`ad-hoc` refers to running Ansible to perform some quick command, using ``/usr/bin/ansible``, rather than the orchestration language, which is ``/usr/bin/ansible-playbook``, in this case we can ensure connectivity by attempting to execute a single command on the remote device::

  ansible -m eos_command -a 'commands=?' -i inventory switch1.example.net -e 'ansible_connection=local' -u admin -k

In the above example we:

* Connect to ``switch1.example.net`` specified in the inventory file ``inventory``
* Use the module ``eos_command``
* Run the command ``?``
* Connect using the username ``admin``
* Inform ansible to prompt for the ssh password by specifying ``-k``

If you have SSH keys configured correctly you can drop the ``-k`` parameter

If the above still fails you can combine it the LINK(Enabling Network logging) section, for example::

  # Specify the location for the log file
  export ANSIBLE_LOG_PATH=~/ansible.log
  # Run with 4*v for connection level verbosity
  ANSIBLE_DEBUG=True ansible -m eos_command -a 'commands=?' -i inventory switch1.example.net -e 'ansible_connection=local' -u admin -k

Then review the log file and find the relevant error message in the rest of this document.

For details on other ways to authenticate see LINKTOAUTHHOWTODOCS.

Troubleshooting Network Modules
===============================

This section covers some of the more common error messages and troubleshooting steps.



Error: "Unable to open shell"
-----------------------------

**Platforms:** Any

This occurs when something happens that prevents a shell from opening on the remote device.

For example:

.. code-block:: yaml

   TASK [ios_system : configure name_servers] *****************************************************************************
   task path:
   fatal: [ios-csr1000v]: FAILED! => {
       "changed": false,
       "failed": true,
       "msg": "unable to open shell",
       "rc": 255
   }

Suggestions to resolve:

Rerun Ansible with extra logging. For example:

:code:`export ANSIBLE_LOG_PATH=~/ansible.log`

:code:`ANISBLE_DEBUG=True ansible-playbook -vvvvv  ...`

Once the task has failed, find the relevant log lines.

For example:

.. code-block:: yaml

  less $ANSIBLE_LOG_PATH
  2017-03-10 15:32:06,173 p=19677 u=fred |  number of connection attempts exceeded, unable to connect to control socket
  2017-03-10 15:32:06,174 p=19677 u=fred |  persistent_connect_interval=1, persistent_connect_retries=10
  2017-03-10 15:32:06,222 p=19669 u=fred |  fatal: [veos01]: FAILED! => {
    "changed": false,

Look for an error message in this document. In this example, the relevant lines are:

.. code-block:: yaml

  number of connection attempts exceeded, unable to connect to control socket
  persistent_connect_interval=1, persistent_connect_retries=10

...indicates a connection timeout has occurred, see next section.

.. notes: Easier to read error messages

   The final version of Ansible 2.3 will include improved logging which will make it easier to identify connection lines in the log


Error: "number of connection attempts exceeded, unable to connect to control socket"
------------------------------------------------------------------------------------

**Platforms:** Any

This occurs when Ansible wasn't able to connect to the remote device and obtain a shell with the timeout.


This information is available when ``ANSIBLE_LOG_PATH`` is set see (FIXMELINKTOSECTION):

.. code-block:: yaml

  less $ANSIBLE_LOG_PATH
  2017-03-10 15:32:06,173 p=19677 u=fred |  number of connection attempts exceeded, unable to connect to control socket
  2017-03-10 15:32:06,174 p=19677 u=fred |  persistent_connect_interval=1, persistent_connect_retries=10
  2017-03-10 15:32:06,222 p=19669 u=fred |  fatal: [veos01]: FAILED! => {

Suggestions to resolve:

Do stuff For example:

.. code-block:: yaml

	Example stuff

Error: "Authentication failed"
------------------------------

**Platforms:** Any

Occurs if the credentials (username, passwords, or ssh keys) passed to ``ansible-connection`` (via ``ansible`` or ``ansible-playbook``) can not be used to connect to the remote device.



For example:

.. code-block:: yaml

   <ios01> ESTABLISH CONNECTION FOR USER: cisco on PORT 22 TO ios01
   <ios01> Authentication failed.


Suggestions to resolve:

If you are specifying credentials via ``password:`` (either directly or via ``provider:``) or the environment variable ``ANSIBLE_NET_PASSWORD`` it is possible that ``paramiko`` (the Python SSH library that Ansible uses) is using ssh keys, and therefore the credentials you are specifying are being ignored. To find out if this is the case, disable "look for keys". This can be done like this:

.. code-block:: yaml

   export ANSIBLE_PARAMIKO_LOOK_FOR_KEYS=False

To make this a permanent change, add the following to your ``ansible.cfg`` file:

.. code-block:: ini

   [paramiko_connection]
   look_for_keys = False





Error: "Unable to enter configuration mode"
-------------------------------------------

**Platforms:** eos and ios

This occurs when you attempt to run a task that requires privileged mode in a user mode shell.

For example:

.. code-block:: yaml

  TASK [ios_system : configure name_servers] *****************************************************************************
  task path:
  fatal: [ios-csr1000v]: FAILED! => {
      "changed": false,
      "failed": true,
     "msg": "unable to enter configuration mode",
      "rc": 255
  }

Suggestions to resolve:

Add ``authorize: yes`` to the task. For example:

.. code-block:: yaml

  - name: configure hostname
    ios_system:
      provider:
        hostname: foo
        authorize: yes
    register: result

If the user requires a password to go into privileged mode, this can be specified with ``auth_pass``; if ``auth_pass`` isn't set, the environment variable ``ANSIBLE_NET_AUTHORIZE`` will be used instead.


Add `authorize: yes` to the task. For example:

.. code-block:: yaml

  - name: configure hostname
    ios_system:
    provider:
      hostname: foo
      authorize: yes
      auth_pass: "{{ mypasswordvar }}"
  register: result



Error: "invalid connection specified, expected connection=local, got ssh"
-------------------------------------------------------------------------

**Platforms:** Any

Network modules require that the connection is set to ``local``.  Any other
connection setting will cause the playbook to fail.  Ansible will now detect
this condition and return an error message:

.. code-block:: yaml

    fatal: [nxos01]: FAILED! => {
        "changed": false,
        "failed": true,
        "msg": "invalid connection specified, expected connection=local, got ssh"
    }


To fix this issue, set the connection value to ``local`` using one of the
following methods:

* Set the play to use ``connection: local``
* Set the task to use ``connection: local``
* Run ansible-playbook using the ``-c local`` setting

Timeouts
--------

All network modules support a timeout value that can be set on a per task
basis.  The timeout value controls the amount of time in seconds before the
task will fail if the command has not returned.  

.. code-block:: yaml
    
    - name: save running-config
      ios_command: 
        commands: copy running-config startup-config
        provider: "{{ cli }}"
        timeout: 30

Some operations take longer than the default 10 seconds to complete.  One good
example is saving the current running config on IOS devices to startup config.
In this case, changing the timeout value form the default 10 seconds to 30
seconds will prevent the task from failing before the command completes
successfully.


Clearing Out Persistent Connections
-----------------------------------

**Platforms:** Any

In Ansible 2.3, persistent connection sockets are stored in ``~/.ansible/pc`` for all network devices.  When an Ansible playbook runs, the persistent socket connection is displayed when verbose output is specified.

``<switch> socket_path: /home/fred/.ansible/pc/f64ddfa760``

To clear out a persistent connection before it times out (the default timeout is 30 seconds
of inactivity), simple delete the socket file.



