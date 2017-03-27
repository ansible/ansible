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

   The list of network platforms that support Persistent Connection will increase over in each release.

Playbook Structure from 2.1 to 2.3
==================================

Ansible 2.3 makes it easier to write playbooks by bringing the (FIXME some term about how layout playbooks and connections FIXME) inline with how Ansible is used to manage Linux and Windows systems. This means that you no longer need to define the connection details in every task (via ``host:`` or ``provider:``, instead you can utilize ssh keys and write shorted playbooks.


That said Ansible 2.3 maintains backwards with playbooks created in Ansible 2.2, so you are not forced to upgrade your playbooks when you upgrade to Ansible 2.3.

Why is this changing
--------------------

In Ansible 2.FIXME specifying when writing network playbooks with credentials directly under the task, or under provider will no longer be supported. This is to make the network modules work in the same way as normal Linux and Windows modules. This has the following advantages

* Easier to understand - same as the rest of Ansible
* Simplified module code - fewer code paths doing similar things
* FIXME add other reasons here


Recap of different connection methods
-------------------------------------
This section demonstrates the different ways to write connect to network devices.

The following examples are all equivalent.

.. note: Which playbook style should I use

   If you are starting Networking in Ansible 2.3 we recommend using FIXME name for 2.3 style FIXME. As that is the format that will be supported long term.

Playbook with provider dict
```````````````````````````

**Version:** Ansible 2.2 - 2.3

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


Note, that if you use this form in Ansible 2.3 you will get the following deprecation messages. This is a reminder that you need to move to the new (FIXME NEED A NAME) 2.3 Style, or use ``provider:``.

.. code-block:: yaml

   [WARNING]: argument username has been deprecated and will be removed in a future version
   [WARNING]: argument host has been deprecated and will be removed in a future version
   [WARNING]: argument password has been deprecated and will be removed in a future version

2.2 Playbook with provider
``````````````````````````

**Version:** Ansible 2.2 - 2.3

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

**Version:** Ansible 2.3

FIXME Detail how to use credentials

.. code-block:: yaml

   - name: Gather facts
     - eos_facts:
         gather_subset: all


By default eos and nxos module use cli (ssh). If you wish to use the API then use the ``transport:`` option, for example:

.. code-block:: yaml

   - name: Gather facts
     - eos_facts:
         gather_subset: all
         transport: eapi



Specifying Credentials
======================

FIXME Detail each of the ways people can specify credentials, where possible this should link back to existing Ansible Documentation (which may need tidying up)

* provider (and vars)
* ssh keys
* command line (``-u someuser -k``)
* what else?


Connection Errors
=================

This section covers troubleshooting connection errors.


"Unable to open shell" error
----------------------------

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

"Authentication failed"
-----------------------

**Platforms:** Any

Occurs if the credentials (username, passwords, or ssh keys) passed to ``ansible-connection`` (via ``ansible`` or ``ansible-playboo``) can not be used to connect to the remote device.



For example:

.. code-block:: yaml

   <ios01> ESTABLISH CONNECTION FOR USER: cisco on PORT 22 TO ios01
   <ios01> Authentication failed.


Suggestions to resolve:

If you are specifying credentials via ``password:`` (either directly or via ``provider:``) or the environment variable ``ANSIBLE_NET_PASSWORD`` it is possible that ``paramiko`` (the Python SSH library that Ansible uses) is using ssh keys, and therefore the credentials you are specifying could be ignored. To find out if this is the case disable "look for keys",

This can be done via:

.. code-block:: yaml

   export ANSIBLE_PARAMIKO_LOOK_FOR_KEYS=False

Or to make this a permanent change add the following to your ``ansible.cfg``

.. code-block:: ini

   [paramiko_connection]
   look_for_keys = False





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

	- name: configure hostname
	  ios_system:
	    hostname: foo
	    authorize: yes
	  register: result

If the user requires a password to go into privileged mode, this can be specified with ``auth_pass``, or if that isn't set the environment variable ``ANSIBLE_NET_AUTHORIZE`` will be used instead.


Add `authorize: yes` to the task. For example:

.. code-block:: yaml

	- name: configure hostname
	  ios_system:
	    hostname: foo
	    authorize: yes
        auth_pass: "{{ mypasswordvar }}"
	  register: result



Got connection X, expected local
--------------------------------

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

