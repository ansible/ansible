.. _network_howto:

***************
Network How-Tos
***************

.. contents:: Topics

Introduction
============

TDB

How-Tos
=======

Connection Methods
------------------

**HERE IS WHERE THE DIFFERENT WAYS TO CONNECT SHOULD LIVE**
Specifying Credentials
======================

In Ansible versions 2.0 to 2.2, network modules support providing connection credentials as top-level arguments in the module. The forthcoming release of Ansible 2.3 introduces a new connection framework that is more tightly integrated into Ansible.

With this new connection framework, we have decided to immediately deprecate the use of top level arguments for passing credentials into network modules.  This applies to all top-level credentials arguments except ``provider``. Platforms that support privilege, such as eos and ios, top-level options ``auth_pass`` and ``authorize`` are still supported. Top-level arguments that have been deprecated (including ``username``, ``host``, and ``password``) will still function, but Ansible will display a warning saying that those arguments have been deprecated and will be removed in a future release.

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


This removes the requirement to encode any credentials into the Playbook, further simplifying the Playbook.

Or you can use SSH keys..


Connecting using SSH Keys
^^^^^^^^^^^^^^^^^^^^^^^^^

TBD: This is the recomended way, ``ssh_keyfile``

Connecting using Command line arguments
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

TBD: ``-u user -k`

Provider Arguments
^^^^^^^^^^^^^^^^^^

TBD

.. code-block:: yaml

   - ios_command:
       commands: show version
       provider:
         host: "{{ inventory_hostname }}"
         username: cisco
         password: mypassword

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


Entering Configuration Mode
----------------------------

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

Where To Get More Help
======================

TBD

