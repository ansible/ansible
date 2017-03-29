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

 * dellos9
 * dellos10
 * eos
 * ios
 * iosxr
 * junos
 * nxos (some)
 * vyos
 * sros (from 2.3 RC2)


.. notes: Future support

   The list of network platforms that support Persistent Connection will increase over in each release.

.. notes: Persistent Connections is for `cli` (ssh), not for API transports.

   The Persistent Connection work added in Ansible 2.3 only applies to `cli transport`. It doesn't apply to APIs such as eos's eapi, nor nxos's nxapi. From Ansible 2.3 using CLI should be faster in most cases than using the API transport. Using CLI also allows you be benefit from using SSH Keys.

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

In Ansible versions 2.0 to 2.2, network modules support providing connection credentials as top-level arguments in the module. The forthcoming release of Ansible 2.3 introduces a new connection framework that is more tightly integrated into Ansible.

With this new connection framework, we have decided to immediately deprecate the use of top level arguments for passing credentials into network modules.  This applies to all top-level credentials arguments except ``provider``. Platforms that support privilege, such as eos and ios, top-level options ``auth_pass`` and ``authorize`` are still supported. Top-level arguments that have been deprecated (including ``username``, ``host``, and ``password``) will still function, but Ansible will display a warning saying that those arguments have been deprecated and will be removed in a future release.

Since the new connection framework in Ansible 2.3 is now completely integrated as an Ansible plugin, you can now pass credential information from the command line in Ansible just as you can for non-network modules.

For example, the old method

.. code-block:: yaml

   - ios_command:
       commands: show version
       host: "{{ inventory_hostname }}"
       username: cisco
       password: cisco

...in Ansible 2.3 can now be written as:

.. code-block:: yaml

    ---
    - hosts: ios_routers
      connection: local
     
      tasks:
        - name: run show version
          ios_command:
        commands: show version


Note that the new task entry does not include any credential information anywhere.  In order to execute the new playbook, the credentials are now taken from the Ansible command line::

 $ ansible-playbook demo.yaml -u cisco -k
 SSH password:

 PLAY [ios01] ***************************************************************

 TASK [ios_command] *********************************************************
 ok: [ios01]

 PLAY RECAP *****************************************************************
 ios01                      : ok=1    changed=0    unreachable=0    failed=0


This removes the requirement to encode any credentials into the Playbook, further simplifying the Playbook.

Anisble Network Roadmap
=======================

To best understand the changes that have gone into Ansible 2.3 it's useful to understand where we've come from and where we are heading.

Ansible 2.3
-----------

 * Introduction of Persistent Connections
 * Deprecation notice of using top-level arguments


Ansible 2.4
------------
become

Ansible future
--------------
Which release will provider go away

Connection Errors
=================

This section covers troubleshooting connection errors.

Errors generally fall into one of the following categories

:Authentication issues: Which fall into:
  * Not correctly specifying credentials
  * Remote device (network switch/router) not falling back to other other authentication methods
:Timeout issues:
  Can occur when trying to pull a large amount of data

Details about how to test
forks/limits/drop to a single ad-hoc command


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


"number of connection attempts exceeded, unable to connect to control socket"
-----------------------------------------------------------------------------

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





"Unable to enter configuration mode"
------------------------------------

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

If the user requires a password to go into privileged mode, this can be specified with ``auth_pass``, or if that isn't set the environment variable ``ANSIBLE_NET_AUTHORIZE`` will be used instead.


Add `authorize: yes` to the task. For example:

.. code-block:: yaml

	- name: configure hostname
	  ios_system:
	    hostname: foo
	    authorize: yes
        auth_pass: "{{ mypasswordvar }}"
	  register: result



"invalid connection specified, expected connection=local, got ssh"
------------------------------------------------------------------

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

Persistent connection sockets are stored in ``~/.ansible/pc`` in Ansible 2.3
for all network devices.  When an Ansible playbook runs the persistent socket
connection displayed when specifying verbose output.

``<switch> socket_path: /home/operations/.ansible/pc/f64ddfa760``

To clear out a persistent connection before it times out (default is 30 seconds
of inactivity), simple delete the socket file.


Inspecting Logs
---------------

**Platforms:** Any

Ansible can be run with high log verbosity by doing:

:code:`export ANSIBLE_LOG_PATH=/tmp/ansible.log`

:code:`ANISBLE_DEBUG=True ansible-playbook -vvvvv  ...`

The log file can be inspected by doing:

:code:`less $ANSIBLE_LOG_PATH`

The log lines generally follow ``using connection plugin network_cli`` in the file, though it's possible some details


Howtos
======

TBD




Using Ansible Ad-hoc To Test
----------------------------

**Platforms:** Any

With the connection plugins introduced in Ansible 2.3, running ad-hoc commands
is relatively easy.  Since the new connection framework is integrated into
Ansible as a plugin, network modules can be run by specifying credential
details at the command line.

.. code:`ansible -m ios_command -a "commands='show version'" -u cisco -k -c local ios01`

The command string above will run the ``ios_command`` module and provide the
argument ``commands`` with the value of ``"show version"``.  The ``-u cisco``
and ``-k`` switches will set the username and prompt for the SSH password
accordingly.  The ``-c local`` will specify the connection type to use is
local finally ``ios01`` is the inventory host to run the command against.  The
resulting output is shown below.

.. code-block:: yaml

	ansible -m ios_command -a "commands='show version'" -u cisco -k -c local ios01
	SSH password:
	ios01 | SUCCESS => {
		"changed": false,
		"stdout": [
			"Cisco IOS Software, IOSv Software (VIOS-ADVENTERPRISEK9-M), Version 15.6(2)T, RELEASE SOFTWARE (fc2)\nTechnical Support: http://www.cisco.com/techsupport\nCopyright (c) 1986-2016 by Cisco Systems, Inc.\nCompiled Tue 22-Mar-16 16:19 by prod_rel_team\n\n\nROM: Bootstrap program is IOSv\n\nios1 uptime is 5 weeks, 1 day, 13 hours, 16 minutes\nSystem returned to ROM by reload\nSystem image file is \"flash0:/vios-adventerprisek9-m\"\nLast reload reason: Unknown reason\n\n\n\nThis product contains cryptographic features and is subject to United\nStates and local country laws governing import, export, transfer and\nuse. Delivery of Cisco cryptographic products does not imply\nthird-party authority to import, export, distribute or use encryption.\nImporters, exporters, distributors and users are responsible for\ncompliance with U.S. and local country laws. By using this product you\nagree to comply with applicable laws and regulations. If you are unable\nto comply with U.S. and local laws, return this product immediately.\n\nA summary of U.S. laws governing Cisco cryptographic products may be found at:\nhttp://www.cisco.com/wwl/export/crypto/tool/stqrg.html\n\nIf you require further assistance please contact us by sending email to\nexport@cisco.com.\n\nCisco IOSv (revision 1.0) with  with 472441K/50176K bytes of memory.\nProcessor board ID 9BNV53XPBXODQRAB0K2SY\n3 Gigabit Ethernet interfaces\nDRAM configuration is 72 bits wide with parity disabled.\n256K bytes of non-volatile configuration memory.\n2097152K bytes of ATA System CompactFlash 0 (Read/Write)\n0K bytes of ATA CompactFlash 1 (Read/Write)\n0K bytes of ATA CompactFlash 2 (Read/Write)\n10080K bytes of ATA CompactFlash 3 (Read/Write)\n\n\n\nConfiguration register is 0x0"
		],
		"stdout_lines": [
			[
				"Cisco IOS Software, IOSv Software (VIOS-ADVENTERPRISEK9-M), Version 15.6(2)T, RELEASE SOFTWARE (fc2)",
				"Technical Support: http://www.cisco.com/techsupport",
				"Copyright (c) 1986-2016 by Cisco Systems, Inc.",
				"Compiled Tue 22-Mar-16 16:19 by prod_rel_team",
				"",
				"",
				"ROM: Bootstrap program is IOSv",
				"",
				"ios1 uptime is 5 weeks, 1 day, 13 hours, 16 minutes",
				"System returned to ROM by reload",
				"System image file is \"flash0:/vios-adventerprisek9-m\"",
				"Last reload reason: Unknown reason",
				"",
				"",
				"",
				"This product contains cryptographic features and is subject to United",
				"States and local country laws governing import, export, transfer and",
				"use. Delivery of Cisco cryptographic products does not imply",
				"third-party authority to import, export, distribute or use encryption.",
				"Importers, exporters, distributors and users are responsible for",
				"compliance with U.S. and local country laws. By using this product you",
				"agree to comply with applicable laws and regulations. If you are unable",
				"to comply with U.S. and local laws, return this product immediately.",
				"",
				"A summary of U.S. laws governing Cisco cryptographic products may be found at:",
				"http://www.cisco.com/wwl/export/crypto/tool/stqrg.html",
				"",
				"If you require further assistance please contact us by sending email to",
				"export@cisco.com.",
				"",
				"Cisco IOSv (revision 1.0) with  with 472441K/50176K bytes of memory.",
				"Processor board ID 9BNV53XPBXODQRAB0K2SY",
				"3 Gigabit Ethernet interfaces",
				"DRAM configuration is 72 bits wide with parity disabled.",
				"256K bytes of non-volatile configuration memory.",
				"2097152K bytes of ATA System CompactFlash 0 (Read/Write)",
				"0K bytes of ATA CompactFlash 1 (Read/Write)",
				"0K bytes of ATA CompactFlash 2 (Read/Write)",
				"10080K bytes of ATA CompactFlash 3 (Read/Write)",
				"",
				"",
				"",
				"Configuration register is 0x0"
			]
		]
	}



Connecting via A Proxy Host
---------------------------

**Platforms:** Any

The new connection framework in Ansible 2.3 no longer supports the use of the
``delegate_to`` directive.  In order to use a bastion or intermediate jump host
to connect to network devices, network modules now support the use of
``ProxyCommand``.

To use ``ProxyCommand`` configure the proxy settings in the Ansible inventory
file to specify the proxy host.

.. code-block:: ini

    [nxos]
    nxos01
    nxos02

    [nxos:vars]
    ansible_ssh_common_args='-o ProxyCommand="ssh -W %h:%p -q bastion01"'


With the configuration above, simply build and run the playbook as normal with
no additional changes necessary.  The network module will now connect to the
network device by first connecting to the host specified in
``ansible_ssh_common_args`` which is ``bastion01`` in the above example.

.. warning: ``delegate_to``

   Note that in Ansible 2.3 ``delegate_to`` is not supported for Network modules.


.. notes: Using ``ProxyCommand`` with passwords via variables

   It is a feature that SSH doesn't support providing passwords via environment variables.
   This is done to prevent secrets from leaking out, for example in ``ps`` output.

   We recommend using SSH Keys, and if needed and ssh-agent, where ever possible.

Clearing Out Persistent Connections
-----------------------------------

TBD

Inspecting Logs
---------------

TBD


Where To Get More Help
======================

TBD

