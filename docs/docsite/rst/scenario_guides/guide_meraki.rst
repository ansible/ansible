.. _meraki_guide:

Cisco Meraki Guide
==================


.. _meraki_guide_intro:

What is Cisco Meraki?
---------------------

Cisco Meraki is an easy to use, cloud based, network infrastructure platform for enterprise environments. While most network hardware uses command line interfaces (CLIs) for configuration, Meraki uses an easy to use Dashboard hosted in the Meraki cloud. No on-premises management hardware or software is required - only the network infrastructure to run your business.

MS Switches
...........

Meraki MS switches come in multiple flavors and form factors. Meraki switches support 10/100/1000/10000 ports, as well as Cisco's mGig technology for 2.5/5/10Gbps copper connectivity. 8, 24, and 48 port flavors are available with PoE (802.3af/802.3at/UPoE) available on many models.

MX Firewalls
............

Meraki's MX firewalls support full layer 3-7 deep packet inspection. MX firewalls are compatible with a variety of VPN technologies including IPSec, SSL VPN, and Meraki's easy-to-use AutoVPN.

MR Wireless Access Points
.........................

MR access points are enterprise class, high performance, access points for the enterprise. MR access points have MIMO technology and integrated beamforming built-in for high performance applications. BLE allows for advanced location applications to be developed with no on-premises analytics platforms.

Using the Meraki modules
------------------------

Meraki modules provide a user-friendly interface to manage your Meraki environment using Ansible. For example, details about SNMP settings for a particular organization can be discovered using the module `meraki_snmp <meraki_snmp_module>`.

.. code-block:: yaml

	- name: Query SNMP settings
	  meraki_snmp:
	  	api_key: abc123
	  	org_name: AcmeCorp
	  	state: query
	  delegate_to: localhost

Information about a particular object can be queried. For example, the `meraki_admin <meraki_admin_module>` module supports

.. code-block:: yaml

	- name: Gather information about Jane Doe
	  meraki_admin:
	  	api_key: abc123
	  	org_name: AcmeCorp
	  	state: query
	  	email: janedoe@email.com
	  delegate_to: localhost

Common Parameters
.................

All Ansible Meraki modules support the following parameters which affect communication with the Meraki Dashboard API. Most of these should only be used by Meraki developers and not the general public.

	host
		Hostname or IP of Meraki Dashboard.

	use_https
		Specifies whether communication should be over HTTPS. (Defaults to ``yes``)

	use_proxy
		Whether to use a proxy for any communication.

	validate_certs
		Determine whether certificates should be validated or trusted. (Defaults to ``yes``)

Meraki Authentication
.....................

All API access with the Meraki Dashboard requires an API key. An API key can be generated from the organization's settings page. Each play in a playbook requires the ``api_key`` parameter to be specified.

The "Vault" feature of Ansible allows you to keep sensitive data such as passwords or keys in encrypted files, rather than as plain text in your playbooks or roles. These vault files can then be distributed or placed in source control. See :ref:`playbooks_vault` for more information.