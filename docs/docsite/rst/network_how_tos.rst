.. _network_howto:

***************
Network How-Tos
***************

.. contents:: Topics

Introduction
============

TDB

Connection Topics
=================

TBD Overview of the different methods and why SSH is recommended.

Specifying Credentials
----------------------

.. note: Which playbook style should I use?

   If you are starting Networking in Ansible 2.3 we recommend using FIXME name for 2.3 style FIXME. As that is the format that will be supported long term.
   Where ever possible we suggest using `cli` with SSH keys.



In Ansible versions 2.0 to 2.2, network modules support providing connection credentials as top-level options;in the module. The forthcoming release of Ansible 2.3 introduces a new connection framework that is more tightly integrated into Ansible.

With this new connection framework, we have decided to immediately deprecate the use of top level options for passing credentials into network modules.  This applies to all top-level credentials options except ``provider''. Top-level arguments that have been deprecated (including ``username``, ``host``, and ``password``) will still function, but Ansible will display a warning saying that those arguments have been deprecated and will be removed in a future release.

Since the new connection framework in Ansible 2.3 is now completely integrated as an Ansible plugin, you can now pass credential information from the command line in Ansible just as you can for non-network modules.

For example, the old method



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


This removes the requirement to encode any credentials into the Playbook, further simplifying the Playbook. Please note that the ``-u`` switch is functionally equivalent to ``ansible_ssh_user`` and the ``-k`` switch is functionally equivalent to ``ansible_ssh_pass``. Meaning these variables do not have to be set via command line, and can be set the same as any variable in ansible.

Or you can use SSH keys..


Connecting using SSH Keys
^^^^^^^^^^^^^^^^^^^^^^^^^

Using SSH keys provides a more secure way to authenticate to network devices
versus the standard password authentication method.   Ansible network modules
support using SSH keys to authenticate to network devices.

.. code-block:: yaml

    - name: use ssh keys to authenticate
      eos_command:
        commands: show version
        provider:
          host: "{{ inventory_hostname }}"
          username: ansible
          ssh_keyfile: ~/.ssh/id_rsa

The example playbook above will use the SSH key specified by the ``ssh_keyfile``
option to authenticate to the remote device.  If logging is enabled, it will
show that SSH keys have been used to authenticate to the remote device.  Look
for the following entry in the log file.

``2017-03-31 11:57:47,958 paramiko.transport Authentication (publickey) successful!``


Connecting using Command line arguments
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

With the new connection framework introduced in Ansible 2.3, running Ansible
ad-hoc commands has been greatly simplified.  In order to use Ansible ad-hoc
commands, specify the authentication parameters using the standard Ansible
command line options.

``ansible -m ios_command -a "commands='show version'" -u cisco -k``

When the above is executed Ansible will prompt for the SSH password (because of
the -k option)

Please note that if you need to enter "enable" mode you will still need to pass those
options in the argument string.

``ansible -m ios_command -a "commands='show version' authorize=True auth_pass=cisco" -u cisco -k``


Top-level options
^^^^^^^^^^^^^^^^^

Since the introduction of the network modules into Ansible, the connection
options have been provided via top-level options in the module.

.. code-block:: yaml

    - name: example of using top-level options for connection properties
      ios_command:
        commands: show version
        host: "{{ inventory_hostname }}"
        username: cisco
        password: cisco
        authorize: yes
        auth_pass: cisco


In addition, the same options could also be provided via a single entry in the
provider option.  With the introduction of the new connection framework,
Ansible has officially deprecated the use of top level connection option in
favor of provider option.  Top-level option will continue to work but
playbooks should be updated to use provider options instead.

When running playbooks in Ansible 2.3 and later, Ansible will display a warning
when top-level options are found

.. code-block:: yaml

   [WARNING]: argument username has been deprecated and will be removed in a future version
   [WARNING]: argument host has been deprecated and will be removed in a future version
   [WARNING]: argument password has been deprecated and will be removed in a future version


.. note: Top-level arguments are deprecated

   We suggest you move away from this form and use ``provider:`` (FIXME LINK) or better yet SSH keys are your earliest convenience. Support for this method will be removed in a future release

Provider Arguments
^^^^^^^^^^^^^^^^^^

In order to making passing repeated credential information into modules,
network modules support a single ``provider`` argument that defines the
necessary key / value pairs for authenticating to network devices.  As of
Ansible 2.3, use of the provider argument is the preferred method for providing
authentication information to network modules.

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


Accessing over API (eapi, nxapi)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Platforms:** eos and nxapi

Some network operating systems support additional command line transports in
addition to SSH.  Most notable Arista EOS and Cisco NX-OS support sending CLi
commands over JSON-RPC using an HTTP/S transport.  Ansible modules for these
devices support those transports as a per-module configurable option.

In order to change the default transport from SSH to using the HTTP/S transport
configure the ``transport`` argument in the provider.  The ``transport``
argument accepts device dependent values for changing the transport (eapi for
EOS based devices and nxapi for NX-OS based devices).


FIXME, Include details regarding ``use_ssl``

FIXME: Detail how to enable eapi & nxapi

.. code-block:: yaml

   - name: Gather facts
     - eos_facts:
         provider:
           host: "{{ inventory_hostname }}"
           username: admin
           password: admin
           transport: eapi


Note: Both ``eapi`` and ``nxapi`` support additional arguments to change the
default behavior of the HTTP/S connection.

When specifying the transport value as either eapi or nxapi, the playbook
implementer can chose to either use ``HTTP`` or ``HTTPS` by setting the value
of ``use_ssl`` to either True or False.

.. code-block:: yaml

   - name: Gather facts
     - eos_facts:
         provider:
           host: "{{ inventory_hostname }}"
           username: admin
           password: admin
           transport: eapi
           use_ssl: no


When configuring the transport to use SSL, it is sometimes desirable to disable
certificate validation.  In order to disable certificate validation use the
``validate_certs`` option.

.. code-block:: yaml

   - name: Gather facts
     - eos_facts:
         provider:
           host: "{{ inventory_hostname }}"
           username: admin
           password: admin
           transport: eapi
           use_ssl: yes
           validate_certs: no

.. warning: Disabling SSL check

    Please be sure you understand the security implications to changing either or both of ``use_ssl: no`` or ``validate_certs: no``.

See the individual module documentation for more information on supported
values and default settings.


FIXME Networking Environment Variables FIXME
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

FIXME This needs documenting somewhere, and most likely with RST field table

The following environment variables are available to Ansible networking modules:

username ANSIBLE_NET_USERNAME
password ANSIBLE_NET_PASSWORD
ssh_keyfile ANSIBLE_NET_SSH_KEYFILE
authorize ANSIBLE_NET_AUTHORIZE
auth_pass ANSIBLE_NET_AUTH_PASS


FIXME, not sure why this is here, need to say why it's relevant and link to the official source (where?) in other Ansible docs

Variables are evaluated in the following order, listed from lowest to highest priority:

* Default
* Environment
* Provider
* Task arguments




Connecting via A Proxy Host (CLI)
---------------------------------

**Platforms:** Any CLI

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

Connecting via A Proxy Host (API)
---------------------------------

**Platforms:** Any API

TBD: Is this something we need to document?


Entering Configuration Mode
===========================

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
            provider:
              authorize: yes
              auth_pass: "{{ mypasswordvar }}"
	  register: result


Conditionals in Networking Modules
====================================

Ansible allows you to use conditionals to control the flow of your playbooks. Ansible networking command modules use the following unique conditional statements.

* ``eq`` - Equal
* ``neq`` - Not equal
* ``gt`` - Greater than
* ``ge`` - Greater than or equal
* ``lt`` - Less than
* ``le`` - Less than or equal
* contains - Object contains specified item


Conditional statements evalute the results from the commands that are
executed remotely on the device.  Once the task executes the command
set, the wait_for argument can be used to evalute the results before
returning control to the Ansible playbook.

FIXME Example needs reviewing

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
FIXME Example needs reviewing
:code:`(result[0].interfaces.Ethernet4.interfaceStatus)` is not equal to
"connected", then the command is retried.  This process continues
until either the condition is satisfied or the number of retries has
expired (by default, this is 10 retries at 1 second intervals).

The commands module can also evaluate more than one set of command
results in an interface.  For instance::

    FIXME Example needs reviewing

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

The wait_for argument must always start with result and then the
command index in [], where 0 is the first command in the commands list,
1 is the second command, 2 is the third and so on.



Using Ansible Ad-hoc To Test
============================

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


