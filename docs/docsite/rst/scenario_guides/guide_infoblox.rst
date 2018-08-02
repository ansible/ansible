.. _nios_guide:

************************
 Infoblox Guide
************************

.. contents:: Topics

This guide describes how to use Ansible with the Infoblox Network Identity Operating System (NIOS).

Introduction
=============
With Ansible integration, you can automate Infoblox Core Network Services for IP address management (IPAM), DNS and DHCP configuration.

Prerequisites
-------------
Before using Ansible nios modules with Infoblox, you must install the ``infoblox-client`` on your Ansible control node:

.. code-block:: bash

    $ sudo pip install infoblox-client

Credentials and authenticating
==============================



Common parameters and settings
==============================



Module list
============
Ansible supports the following modules for NIOS:

- `nios_host_record <http://docs.ansible.com/ansible/latest/modules/nios_host_record_module.html>`_ - configure host records
- `nios_network <http://docs.ansible.com/ansible/latest/modules/nios_network_module.html>`_ - configure networking objects
- `nios_network_view <http://docs.ansible.com/ansible/latest/modules/nios_network_view_module.html>`_ - configure networking views
- `nios_dns_view <http://docs.ansible.com/ansible/latest/modules/nios_dns_view_module.html>`_ - configure DNS views
- `nios_zone <http://docs.ansible.com/ansible/latest/modules/nios_zone_module.html>`_ - configure DNS zones

Each module includes simple documented example tasks for how to use them.


NIOS lookup plugin
==================

The `nios <https://docs.ansible.com/ansible/devel/plugins/lookup/nios.html>`_ lookup plugin uses the Infoblox WAPI API to fetch NIOS specified objects, for example network views, DNS views, and host records.

.. note:: You must run this lookup locally by specifying ``connection: local``.

Retrieving a host record
------------------------

This example task uses the ``nios`` lookup to retrieve the host record for a host called ``leaf01``:

.. code-block:: yaml

    - name: fetch host leaf01
          set_fact:
            host: "{{ lookup('nios', 'record:host', filter={'name': 'leaf01'}, provider=nios_provider) }}"

This task is part of an example `get_host_record.yml <https://github.com/network-automation/infoblox_ansible/blob/master/lookup_playbooks/get_host_record.yml>`_ lookup playbook.

If you run this example ``get_host_record.yml`` playbook, you should see results similar to the following:

.. code-block:: bash

    $ ansible-playbook get_host_record.yml

    PLAY [localhost] ***************************************************************************************

    TASK [fetch host leaf01] ******************************************************************************
    ok: [localhost]

    TASK [check the leaf01 return variable] *************************************************************
    ok: [localhost] => {
    <SNIPPET, REST OF OUTPUT REMOVED FOR BREVITY>
        "host": {
            "ipv4addrs": [
                {
                    "configure_for_dhcp": false,
                    "host": "leaf01",
                    "ipv4addr": "192.168.1.11"
                }
            ],
        }
    }

    TASK [debug specific variable (ipv4 address)] ******************************************************
    ok: [localhost] => {
        "host.ipv4addrs[0].ipv4addr": "192.168.1.11"
    }

    TASK [fetch host leaf02] ******************************************************************************
    ok: [localhost]

    TASK [check the leaf02 return variable] *************************************************************
    ok: [localhost] => {
    <SNIPPET, REST OF OUTPUT REMOVED FOR BREVITY>

        "host": {
            "ipv4addrs": [
                {
                    "configure_for_dhcp": false,
                    "host": "leaf02",
                    "ipv4addr": "192.168.1.12"
                }
            ],
        }
    }

    PLAY RECAP ******************************************************************************************
    localhost                  : ok=5    changed=0    unreachable=0    failed=0

The output above shows the host record for ``leaf01`` that was retrieved by the ``nios`` lookup plugin. This playbook saves the information in variables that you can use in other playbooks. This allows you to use Infoblox as a single source of truth to gather and use information that may be changing dynamically. See `Ansible variables <http://docs.ansible.com/ansible/latest/playbooks_variables.html>`_ for more information on using Ansible variables.

Dynamic inventory script
========================

You can use the Infoblox dynamic inventory script to import your network node inventory with Infoblox NIOS. To gather the inventory from Infoblox, you need two files:

- `infoblox.yaml <https://raw.githubusercontent.com/ansible/ansible/devel/contrib/inventory/infoblox.yaml>`_ - A file that specifies the NIOS provider arguments and optional filters.
  - `infoblox.py <https://raw.githubusercontent.com/ansible/ansible/devel/contrib/inventory/infoblox.py>`_ - The python script that retrieves the NIOS inventory.

To use the Infoblox dynamic inventory script:

1. Download the files and save them in the ``/etc/ansible`` directory.
2. Modify the ``infoblox.yaml`` file with your NIOS credentials.
3. Change the permissions on the python file to make it executable:

.. code-block:: bash

    $ sudo chmod +x /etc/ansible/infoblox.py

3. Optionally, test the script:

.. code-block:: bash

   $ python infoblox.py
   {
       " ": {
           "hosts": [
               "leaf01",
               "leaf02",
               "leaf03",
               "leaf04",
               "spine01",
               "spine02"
           ]
       },
   <...output omitted...>

See `Working with Dynamic Inventory <https://docs.ansible.com/ansible/devel/user_guide/intro_dynamic_inventory.html>`_ for more details.

Use Cases
=========

Creating a subnet and forward DNS zone
--------------------------------------

Creating a host record for the gateway address
----------------------------------------------

Example: Provisioning a grid master
-----------------------------------

Provisioning a grid member
--------------------------

Limitations and known issues
============================

.. seealso::

  `Infoblox website <https://www.infoblox.com//>`_
      The Infoblox website
  `Infoblox and Ansible Deployment Guide <https://www.infoblox.com/resources/deployment-guides/infoblox-and-ansible-integration>`_
      The deployment guide for Ansible integration provided by Infoblox.
  `Infoblox Integration in Ansible 2.5 <https://www.ansible.com/blog/infoblox-integration-in-ansible-2.5>`_
      Ansible blog post about Infoblox.
  `Ansible NIOS modules <https://docs.ansible.com/ansible/latest/modules/list_of_net_tools_modules.html>`_
      The list of supported NIOS modules, with examples.
  `Infoblox Ansible Examples <https://github.com/network-automation/infoblox_ansible>`_
      Infoblox example playbooks.
