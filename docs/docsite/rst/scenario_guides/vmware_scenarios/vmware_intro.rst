.. _vmware_ansible_intro:

**********************************
Introduction to Ansible for VMware
**********************************

.. contents:: Topics

Introduction
============

Ansible provides various modules to manage VMware infrastructure, which includes datacenter, cluster,
host system and virtual machine.

Requirements
============

Ansible VMware modules are written on top of `pyVmomi <https://github.com/vmware/pyvmomi>`_.
pyVmomi is the Python SDK for the VMware vSphere API that allows user to manage ESX, ESXi,
and vCenter infrastructure. You can install pyVmomi using pip:

.. code-block:: bash

    $ pip install pyvmomi

Ansible VMware modules leveraging latest vSphere(6.0+) features are using `vSphere Automation Python SDK <https://github.com/vmware/vsphere-automation-sdk-python>`_. The vSphere Automation Python SDK also has client libraries, documentation, and sample code for VMware Cloud on AWS Console APIs, NSX VMware Cloud on AWS integration APIs, VMware Cloud on AWS site recovery APIs, NSX-T APIs.

You can install vSphere Automation Python SDK using pip:

.. code-block:: bash

     $ pip install --upgrade git+https://github.com/vmware/vsphere-automation-sdk-python.git

Note:
   Installing vSphere Automation Python SDK also installs ``pyvmomi``. A separate installation of ``pyvmomi`` is not required.
   
vmware_guest module
===================

The :ref:`vmware_guest<vmware_guest_module>` module manages various operations related to virtual machines in the given ESXi or vCenter server.


.. seealso::

    `pyVmomi <https://github.com/vmware/pyvmomi>`_
        The GitHub Page of pyVmomi
    `pyVmomi Issue Tracker <https://github.com/vmware/pyvmomi/issues>`_
        The issue tracker for the pyVmomi project
    `govc <https://github.com/vmware/govmomi/tree/master/govc>`_
        govc is a vSphere CLI built on top of govmomi
    :ref:`working_with_playbooks`
        An introduction to playbooks

