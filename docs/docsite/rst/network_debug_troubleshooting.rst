.. _network_debug_troubleshooting:

***************************************
Network Debug and Troubleshooting Guide
***************************************

.. contents:: Topics

Introduction
============

This section discusses how to debug and troubleshoot network modules.

Persistent Connections
======================
Before diving into the technical detail of how to troubleshoot it can be useful to understand how Ansible communicates with the remote network device.

As of version 2.3, Ansible includes support for `persistent connections`. Persistent connections are useful for playbooks with multiple tasks that require multiple SSH connections. In previous releases, these SSH connections had to be established and destroyed each time a task was run, which was inefficient. Persistent connections allows an SSH connection to stay active across multiple Ansible tasks and plays, elimintating the need to spend time establishing and destroying the connection. This is done by keeping a Linux socket open, via a daemon process called ``ansible-connection``.

Connection Errors
=================

This section covers troubleshooting connection errors.


"Unable to open shell" error
----------------------------

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

:code:`export ANSIBLE_LOG_PATH=/tmp/ansible.log`

Rerun ansible with extra debugging. For example:

:code:`ANISBLE_DEBUG=True ansible-playbook -vvvvv  ...`

Once the task has failed, find the relevant log lines:

:code:`grep  -e "^<" $ANSIBLE_LOG_PATH`

For example, the following output:

.. code-block:: yaml

  grep FIXME $ANSIBLE_LOG_PATH
  2017-03-10 15:32:06,173 p=19677 u=fred |  number of connection attempts exceeded, unable to connect to control socket
  2017-03-10 15:32:06,174 p=19677 u=fred |  persistent_connect_interval=1, persistent_connect_retries=10
  2017-03-10 15:32:06,222 p=19669 u=fred |  fatal: [veos01]: FAILED! => {
    "changed": false,

Look for error message in this document, in this case the relevant lines are

.. code-block:: yaml

  number of connection attempts exceeded, unable to connect to control socket
  persistent_connect_interval=1, persistent_connect_retries=10

...indicates a connection timeout.


number of connection attempts exceeded, unable to connect to control socket
----------------------------------------------------------------------------

This occurs when Ansible wasn't able to connect to the remote device and obtain a shell with the timeout.


This information is available when ``ANSIBLE_LOG_PATH`` is set see (FIXMELINKTOSECTION):

.. code-block:: yaml

  grep FIXME $ANSIBLE_LOG_PATH
  2017-03-10 15:32:06,173 p=19677 u=fred |  number of connection attempts exceeded, unable to connect to control socket
  2017-03-10 15:32:06,174 p=19677 u=fred |  persistent_connect_interval=1, persistent_connect_retries=10
  2017-03-10 15:32:06,222 p=19669 u=fred |  fatal: [veos01]: FAILED! => {

Suggestions to resolve:

Do stuff For example:

.. code-block:: yaml

	Example stuff


Unable to enter configuration mode
----------------------------------

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

Add `authorize: yes` to the task. For example:

.. code-block:: yaml

	- name: configure hostname
	  ios_system:
	    hostname: foo
	    authorize: yes
	  register: result



Using Ansible Ad-hoc To Test
----------------------------

TBD


Connecting via A Proxy Host
---------------------------

TBD

Clearing Out Persistent Connections
-----------------------------------

TBD

Inspecting Logs
---------------

TBD


Howtos
======

TBD




Using Ansible Ad-hoc To Test
----------------------------

TBD


Connecting via A Proxy Host
---------------------------

TBD

Clearing Out Persistent Connections
-----------------------------------

TBD

Inspecting Logs
---------------

TBD


Where To Get More Help
======================

TBD

