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

NIOS lookup plugin
==================


Dynamic inventory script
========================

Use Cases
=========

Creating a subnet and forward DNS zone
---------

Creating a host record for the gateway address
-----------

Example: Provisioning a grid master
-----------

Provisioning a grid member
------------

Limitations and known issues
============================

.. seealso::
  
