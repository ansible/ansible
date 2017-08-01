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
:Timeout issues:
  * Can occur when trying to pull a large amount of data
  * May actually be masking a authentication issue
:Playbook issues:
  * Use of ``delegate_to``, instead of ``ProxyCommand``
  * Not using ``connection: local``


.. warning: ``unable to open shell`

  The ``unable to open shell`` message is new in Ansible 2.3, it means that the ``ansible-connection`` daemon has not been able to successfully
  talk to the remote network device. This generally means that there is an authentication issue. See the "Authentication and connection issues" section
  in this document for more information.

.. _enable_network_logging:

Enabling Networking logging and how to read the logfile
-------------------------------------------------------

**Platforms:** Any

Ansible 2.3 features improved logging to help diagnose and troubleshoot issues regarding Ansible Networking modules.

Because logging is very verbose it is disabled by default. It can be enabled via the ``ANSIBLE_LOG_PATH`` and ``ANISBLE_DEBUG`` options::

   # Specify the location for the log file
   export ANSIBLE_LOG_PATH=~/ansible.log
   # Enable Debug
   export ANSIBLE_DEBUG=True

   # Run with 4*v for connection level verbosity
   ansible-playbook -vvvv ...

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


.. note: Port None ``creating new control socket for host veos01:None``

   If the log reports the port as ``None`` this means that the default port is being used.
   A future Ansible release will improve this message so that the port is always logged.

Because the log files are verbose, you can use grep to look for specific information. For example, once you have identified the ```pid`` from the ``creating new control socket for host`` line you can search for other connection log entries::

  grep "p=28990" $ANSIBLE_LOG_PATH

Isolating an error
------------------

**Platforms:** Any

As with any effort to troubleshoot it's important to simplify the test case as much as possible.

For Ansible this can be done by ensuring you are only running against one remote device:

* Using ``ansible-playbook --limit switch1.example.net...``
* Using an ad-hoc ``ansible`` command

`ad-hoc` refers to running Ansible to perform some quick command using ``/usr/bin/ansible``, rather than the orchestration language, which is ``/usr/bin/ansible-playbook``. In this case we can ensure connectivity by attempting to execute a single command on the remote device::

  ansible -m eos_command -a 'commands=?' -i inventory switch1.example.net -e 'ansible_connection=local' -u admin -k

In the above example, we:

* connect to ``switch1.example.net`` specified in the inventory file ``inventory``
* use the module ``eos_command``
* run the command ``?``
* connect using the username ``admin``
* inform ansible to prompt for the ssh password by specifying ``-k``

If you have SSH keys configured correctly, you don't need to specify the ``-k`` parameter

If the connection still fails you can combine it with the enable_network_logging parameter. For example::

   # Specify the location for the log file
   export ANSIBLE_LOG_PATH=~/ansible.log
   # Enable Debug
   export ANSIBLE_DEBUG=True
   # Run with 4*v for connection level verbosity
   ansible -m eos_command -a 'commands=?' -i inventory switch1.example.net -e 'ansible_connection=local' -u admin -k

Then review the log file and find the relevant error message in the rest of this document.

.. For details on other ways to authenticate, see LINKTOAUTHHOWTODOCS.

.. _unable_to_open_shell:

Category "Unable to open shell"
===============================


**Platforms:** Any

The ``unable to open shell`` message is new in Ansible 2.3. This message means that the ``ansible-connection`` daemon has not been able to successfully talk to the remote network device. This generally means that there is an authentication issue. It is a "catch all" message, meaning you need to enable ``ANSIBLE_LOG_PATH`` to find the underlying issues.



For example:

.. code-block:: none

  TASK [prepare_eos_tests : enable cli on remote device] **************************************************
  fatal: [veos01]: FAILED! => {"changed": false, "failed": true, "msg": "unable to open shell"}


or:


.. code-block:: none

   TASK [ios_system : configure name_servers] *************************************************************
   task path:
   fatal: [ios-csr1000v]: FAILED! => {
       "changed": false,
       "failed": true,
       "msg": "unable to open shell",
   }

Suggestions to resolve:

Follow the steps detailed in enable_network_logging_.

Once you've identified the error message from the log file, the specific solution can be found in the rest of this document.



Error: "[Errno -2] Name or service not known"
---------------------------------------------

**Platforms:** Any

Indicates that the remote host you are trying to connect to can not be reached

For example:

.. code-block:: yaml

   2017-04-04 11:39:48,147 p=15299 u=fred |  control socket path is /home/fred/.ansible/pc/ca5960d27a
   2017-04-04 11:39:48,147 p=15299 u=fred |  current working directory is /home/fred/git/ansible-inc/stable-2.3/test/integration
   2017-04-04 11:39:48,147 p=15299 u=fred |  using connection plugin network_cli
   2017-04-04 11:39:48,340 p=15299 u=fred |  connecting to host veos01 returned an error
   2017-04-04 11:39:48,340 p=15299 u=fred |  [Errno -2] Name or service not known


Suggestions to resolve:

* If you are using the ``provider:`` options ensure that it's suboption ``host:`` is set correctly.
* If you are not using ``provider:`` nor top-level arguments ensure your inventory file is correct.





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


Error: "connecting to host <hostname> returned an error" or "Bad address"
-------------------------------------------------------------------------

This may occur if the SSH fingerprint hasn't been added to Paramiko's (the Python SSH library) know hosts file.

When using persistent connections with Paramiko, the connection runs in a background process.  If the host doesn't already have a valid SSH key, by default Ansible will prompt to add the host key.  This will cause connections running in background processes to fail.

For example:

.. code-block:: yaml

   2017-04-04 12:06:03,486 p=17981 u=fred |  using connection plugin network_cli
   2017-04-04 12:06:04,680 p=17981 u=fred |  connecting to host veos01 returned an error
   2017-04-04 12:06:04,682 p=17981 u=fred |  (14, 'Bad address')
   2017-04-04 12:06:33,519 p=17981 u=fred |  number of connection attempts exceeded, unable to connect to control socket
   2017-04-04 12:06:33,520 p=17981 u=fred |  persistent_connect_interval=1, persistent_connect_retries=30


Suggestions to resolve:

Use ``ssh-keyscan`` to pre-populate the known_hosts. You need to ensure the keys are correct.

.. code-block:: shell

   ssh-keyscan veos01


or

You can tell Ansible to automatically accept the keys

Environment variable method::

  export ANSIBLE_PARAMIKO_HOST_KEY_AUTO_ADD=True
  ansible-playbook ...

``ansible.cfg`` method:

ansible.cfg

.. code-block: ini

  [paramiko_connection]
  host_key_auto_add = True



.. warning: Security warning

   Care should be taken before accepting keys.

Error: "No authentication methods available"
--------------------------------------------

For example:

.. code-block:: yaml

   2017-04-04 12:19:05,670 p=18591 u=fred |  creating new control socket for host veos01:None as user admin
   2017-04-04 12:19:05,670 p=18591 u=fred |  control socket path is /home/fred/.ansible/pc/ca5960d27a
   2017-04-04 12:19:05,670 p=18591 u=fred |  current working directory is /home/fred/git/ansible-inc/ansible-workspace-2/test/integration
   2017-04-04 12:19:05,670 p=18591 u=fred |  using connection plugin network_cli
   2017-04-04 12:19:06,606 p=18591 u=fred |  connecting to host veos01 returned an error
   2017-04-04 12:19:06,606 p=18591 u=fred |  No authentication methods available
   2017-04-04 12:19:35,708 p=18591 u=fred |  connect retry timeout expired, unable to connect to control socket
   2017-04-04 12:19:35,709 p=18591 u=fred |  persistent_connect_retry_timeout is 15 secs


Suggestions to resolve:

No password or SSH key supplied

Clearing Out Persistent Connections
-----------------------------------

**Platforms:** Any

In Ansible 2.3, persistent connection sockets are stored in ``~/.ansible/pc`` for all network devices.  When an Ansible playbook runs, the persistent socket connection is displayed when verbose output is specified.

``<switch> socket_path: /home/fred/.ansible/pc/f64ddfa760``

To clear out a persistent connection before it times out (the default timeout is 30 seconds
of inactivity), simple delete the socket file.



Timeout issues
==============

Timeouts
--------
Persistent connection idle timeout:

For example:

.. code-block:: yaml

   2017-04-04 12:19:05,670 p=18591 u=fred |  persistent connection idle timeout triggered, timeout value is 30 secs

Suggestions to resolve:

Increase value of presistent connection idle timeout.
.. code-block:: yaml

   export ANSIBLE_PERSISTENT_CONNECT_TIMEOUT=60

To make this a permanent change, add the following to your ``ansible.cfg`` file:

.. code-block:: ini

   [persistent_connection]
   connect_timeout = 60

Command timeout:
For example:

.. code-block:: yaml

   2017-04-04 12:19:05,670 p=18591 u=fred |  command timeout triggered, timeout value is 10 secs

Suggestions to resolve:

Options 1:
Increase value of command timeout in configuration file or by setting enviornment variable.
Note: This value should be less than persistent connection idle timeout ie. connect_timeout

.. code-block:: yaml

   export ANSIBLE_PERSISTENT_COMMAND_TIMEOUT=30

To make this a permanent change, add the following to your ``ansible.cfg`` file:

.. code-block:: ini

   [persistent_connection]
   command_timeout = 30

Option 2:
Increase command timeout per task basis. All network modules support a
timeout value that can be set on a per task basis.
The timeout value controls the amount of time in seconds before the
task will fail if the command has not returned.

For example:

.. FIXME: Detail error here

Suggestions to resolve:

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
Note: This value should be less than persistent connection idle timeout ie. connect_timeout

Persistent socket connect timeout:
For example:

.. code-block:: yaml

   2017-04-04 12:19:35,708 p=18591 u=fred |  connect retry timeout expired, unable to connect to control socket
   2017-04-04 12:19:35,709 p=18591 u=fred |  persistent_connect_retry_timeout is 15 secs

Suggestions to resolve:

Increase value of presistent connection idle timeout.
Note: This value should be greater than SSH timeout ie. timeout value under defaults
section in configuration file and less than the value of the persistent
connection idle timeout (connect_timeout)

.. code-block:: yaml

   export ANSIBLE_PERSISTENT_CONNECT_RETRY_TIMEOUT=30

To make this a permanent change, add the following to your ``ansible.cfg`` file:

.. code-block:: ini

   [persistent_connection]
   connect_retry_timeout = 30



Playbook issues
===============

This section details issues are caused by issues with the Playbook itself.

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


.. delete_to not honoured
   ----------------------
   
   FIXME Do we get an error message
   
   FIXME Link to howto
   
   
   
   
   fixmes
   ======
   
   Error: "number of connection attempts exceeded, unable to connect to control socket"
   ------------------------------------------------------------------------------------
   
   **Platforms:** Any
   
   This occurs when Ansible wasn't able to connect to the remote device and obtain a shell with the timeout.
   
   
   This information is available when ``ANSIBLE_LOG_PATH`` is set see (FIXMELINKTOSECTION):
   
   .. code-block:: yaml
   
     less $ANSIBLE_LOG_PATH
     2017-03-10 15:32:06,173 p=19677 u=fred |  connect retry timeout expired, unable to connect to control socket
     2017-03-10 15:32:06,174 p=19677 u=fred |  persistent_connect_retry_timeout is 15 secs
     2017-03-10 15:32:06,222 p=19669 u=fred |  fatal: [veos01]: FAILED! => {
   
   Suggestions to resolve:
   
   Do stuff For example:
   
   .. code-block:: yaml
   
   	Example stuff
   
