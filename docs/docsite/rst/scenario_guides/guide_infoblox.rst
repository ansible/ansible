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
------------
Before using Ansible nios modules with Infoblox, you must install the infoblox-client on your Ansible control node:

.. code-block:: bash

    $ sudo pip install infoblox-client

Credentials and authenticating
==============================



Common parameters and settings
==============================



Module list
============
Ansible supports the following modules for ``nios``:

- `nios_host_record <http://docs.ansible.com/ansible/latest/modules/nios_host_record_module.html>`_ - configure host records
- `nios_network <http://docs.ansible.com/ansible/latest/modules/nios_network_module.html>`_ - configure networking objects
- `nios_network_view <http://docs.ansible.com/ansible/latest/modules/nios_network_view_module.html>`_ - configure networking views
- `nios_dns_view <http://docs.ansible.com/ansible/latest/modules/nios_dns_view_module.html>`_ - configure DNS views
- `nios_zone <http://docs.ansible.com/ansible/latest/modules/nios_zone_module.html>`_ - configure DNS zones

Each module includes simple documented example tasks for how to use them.


NIOS lookup plugin
==================


Dynamic inventory script
========================

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
