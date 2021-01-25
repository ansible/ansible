.. _vmware_rest_authentication:

*******************************************
How to configure the vmware_rest collection
*******************************************

.. contents::
  :local:


Introduction
============

The vcenter_rest modules need to be authenticated. There are two different

Environment variables
=====================

.. note::
    This solution requires that you call the modules from the local machine.

You need to export some environment variables in your shell before you call the modules.

.. code-block:: shell

    $ export VMWARE_HOST=vcenter.test
    $ export VMWARE_USER=myvcenter-user
    $ export VMWARE_password=mypassword
    $ ansible-playbook my-playbook.yaml

Module parameters
=================

All the vcenter_rest modules accept the following arguments:

- ``vcenter_host``
- ``vcenter_username``
- ``vcenter_password``


Ignore SSL certificate error
============================

It's common to run a test environment without a proper SSL certificate configuration.

To ignore the SSL error, you can use the ``vcenter_validate_certs: no`` argument or
``export VMWARE_VALIDATE_CERTS=no`` to set the environment variable. 
