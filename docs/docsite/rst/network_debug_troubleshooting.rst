.. _network_debug_troubleshooting:

***************************************
Network Debug and Troubleshooting Guide
***************************************

.. contents:: Topics

Introduction
============

Starting with Ansible version 2.1, you can now use the familiar Ansible models of playbook authoring and module development to manage heterogenous networking devices. Ansible supports a growing number of network devices using both CLI over SSH and API (when available) transports.

This section discusses how to debug and troubleshoot network modules in Ansible 2.3.





Troubleshooting Network Modules
===============================

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

Ansible 2.3 feature improved logging to help diagnose and troubleshoot issues regarding Ansible Networking modules.

As the logging is very verbose it is disabled by default, it an be enable via the ``ANSIBLE_LOG_PATH`` and ``ANISBLE_DEBUG`` options::

   # Specify the location for the log file
   export ANSIBLE_LOG_PATH=~/ansible.log

   # Run with 4*v for connection level verbosity
   ANSIBLE_DEBUG=True ansible-playbook -vvvv ...

After ansible has finished running you can inspect the log file:

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
* ``creating new control socket for host veos01:22 as user admin``
* ``control socket path is`` location on disk where the persistent connection socket is created
* ``using connection plugin network_cli`` Informs you that persistent connection is being used
* ``connection established to veos01 in 0:00:22.580626`` Time taken to obtain a shell on the remote device

If the log file has a lot of information in you can look up the `pid` and grep for that, for example::

  grep "p=28990" $ANSIBLE_LOG_PATH



Isolating the error
-------------------

**Platforms:** Any

TBD Troubleshooting best practice - Single machine, use ad-hoc, etc

Use of ``--limit`` and ad-hoc


When combined with logging...

FIXME
* Set ANSIBLE_LOG_PATH
* Delete socket
* ad-hoc

Reference back to `how to read logfile`



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

Rerun ansible extra logging. For example:

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

Look for error message in this document, in this case the relevant lines are

.. code-block:: yaml

  number of connection attempts exceeded, unable to connect to control socket
  persistent_connect_interval=1, persistent_connect_retries=10

...indicates a connection timeout has occurred, see next section.

.. notes: Easier to read error messages

   The final Ansible 2.3 will include improved logging which will make it easier to identify connection lines in the log


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

Occurs if the credentials (username, passwords, or ssh keys) passed to ``ansible-connection`` (via ``ansible`` or ``ansible-playboo``) can not be used to connect to the remote device.



For example:

.. code-block:: yaml

   <ios01> ESTABLISH CONNECTION FOR USER: cisco on PORT 22 TO ios01
   <ios01> Authentication failed.


Suggestions to resolve:

If you are specifying credentials via ``password:`` (either directly or via ``provider:``) or the environment variable ``ANSIBLE_NET_PASSWORD`` it is possible that ``paramiko`` (the Python SSH library that Ansible uses) is using ssh keys, and therefore the credentials you are specifying could be ignored. To find out if this is the case, disable "look for keys".

This can be done via:

.. code-block:: yaml

   export ANSIBLE_PARAMIKO_LOOK_FOR_KEYS=False

To make this a permanent change, add the following to your ``ansible.cfg``

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
	    hostname: foo
	    authorize: yes
	  register: result

If the user requires a password to go into privileged mode, this can be specified with ``auth_pass``; if ``auth_pass`` isn't set the environment variable ``ANSIBLE_NET_AUTHORIZE`` will be used instead.


Add `authorize: yes` to the task. For example:

.. code-block:: yaml

	- name: configure hostname
	  ios_system:
	    hostname: foo
	    authorize: yes
        auth_pass: "{{ mypasswordvar }}"
	  register: result



Error: "invalid connection specified, expected connection=local, got ssh"
-------------------------------------------------------------------------

**Platforms:** Any

Network modules require the connection to be set to ``local``.  Any other
connection setting will cause the playbook to fail.  Ansible will now detect
this condition and return an error message.

.. code-block:: yaml

    fatal: [nxos01]: FAILED! => {
        "changed": false,
        "failed": true,
        "msg": "invalid connection specified, expected connection=local, got ssh"
    }


To fix this issue set the connection value to ``local`` using one of the
following ways.

* Set the play to use ``connection: local``
* Set the task to use ``connection: local``
* Run ansible-playbook using the ``-c local`` setting

Timeouts
--------

TDB Detail when to use the ``timeout:`` option

Clearing Out Persistent Connections
-----------------------------------

**Platforms:** Any

Persistent connection sockets are stored in ``~/.ansible/pc`` in Ansible 2.3
for all network devices.  When an Ansible playbook runs the persistent socket
connection displayed when specifying verbose output.

``<switch> socket_path: /home/operations/.ansible/pc/f64ddfa760``

To clear out a persistent connection before it times out (default is 30 seconds
of inactivity), simple delete the socket file.



