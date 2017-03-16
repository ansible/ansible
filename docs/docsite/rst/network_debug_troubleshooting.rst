.. _network_debug_troubleshooting:

***************************************
Network Debug and Troubleshooting Guide
***************************************

.. contents:: Topics

Introduction
============

This section discusses how to debug and troubleshoot network modules in Ansible 2.3.

Persistent Connections
======================
Before diving into the technical detail of how to troubleshoot it can be useful to understand how Ansible communicates with the remote network device.

As of version 2.3, Ansible includes support for `persistent connections`. Persistent connections are useful for playbooks with multiple tasks that require multiple SSH connections. In previous releases, these SSH connections had to be established and destroyed each time a task was run, which was inefficient. Persistent connections allows an SSH connection to stay active across multiple Ansible tasks and plays, elimintating the need to spend time establishing and destroying the connection. This is done by keeping a Linux socket open, via a daemon process called ``ansible-connection``.

Persistent Connection had been enable for the following groups of modules:

 * eos
 * ios
 * iosxr
 * junos
 * nxos (some)
 * vyos
 * sros (from 2.3 RC2)


.. notes: Future support

   The list of network platforms that support Persistent Connection will increase over time.OK

Playbook Structure from 2.1 to 2.3
==================================

FIXME High level description of change

Example playbooks
-----------------

2.2 Playbook with provider dict
```````````````````````````````

``group_vars/eos.yml``

.. code-block:: yaml

   ---
   cli:
     host: "{{ ansible_host }}"
     username: "{{ eos_cli_user | default('admin') }}"
     password: "{{ eos_cli_pass | default('admin') }}"
     transport: cli


.. code-block:: yaml

   - name: Gather facts
     - eos_facts:
         gather_subset: all
         provider: "{{ cli }}"

2.2 Playbook with provider
``````````````````````````

.. code-block:: yaml

   - name: Gather facts
     - eos_facts:
         gather_subset: all
         provider:
           username: myuser
           password: "{{ networkpassword }}"
           transport: cli
           host: "{{ ansible_host }}"

2.3 Playbook
````````````

.. code-block:: yaml

   - name: Gather facts
     - eos_facts:
         gather_subset: all

# FIXME Add notes about eapi & nxos


These all do the same thing

These all work in 2.3

Why the change to #3

When will #1 and #2 stop working

If you are starting from fresh in 2.3 use #3




Connection Errors
=================

This section covers troubleshooting connection errors.


"Unable to open shell" error
----------------------------

**Platforms:** Any

This occurs when something happens that prevents a shell from opening on the remote device.

For example:

.. code-block:: yaml
   :emphasize-lines: 6

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


number of connection attempts exceeded, unable to connect to control socket
----------------------------------------------------------------------------

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


Unable to enter configuration mode
----------------------------------

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

Add `authorize: yes` to the task. For example:

.. code-block:: yaml
   :emphasize-lines: 4

	- name: configure hostname
	  ios_system:
	    hostname: foo
	    authorize: yes
	  register: result

If the user requires a password to go into privileged mode, this can be specified with ``auth_pass``, or if that isn't set the environment variable ``ANSIBLE_NET_AUTHORIZE`` will be used instead.


Add `authorize: yes` to the task. For example:

.. code-block:: yaml
   :emphasize-lines: 4,5

	- name: configure hostname
	  ios_system:
	    hostname: foo
	    authorize: yes
        auth_pass: "{{ mypasswordvar }}"
	  register: result



Got connection X, expected local
--------------------------------

**Platforms:** Any

FIXME: Add both error messages



Clearing Out Persistent Connections
-----------------------------------

**Platforms:** Any

TBD

Inspecting Logs
---------------

**Platforms:** Any

TBD


Howtos
======

TBD




Using Ansible Ad-hoc To Test
----------------------------

**Platforms:** Any

TBD


Connecting via A Proxy Host
---------------------------

**Platforms:** Any


http://docs.ansible.com/ansible/faq.html#how-do-i-configure-a-jump-host-to-access-servers-that-i-have-no-direct-access-to


.. warning: ``delegate_to``

   Note that in Ansible 2.3 ``delegate_to`` is not supported for Network modules.

Clearing Out Persistent Connections
-----------------------------------

TBD

Inspecting Logs
---------------

TBD


Where To Get More Help
======================

TBD

