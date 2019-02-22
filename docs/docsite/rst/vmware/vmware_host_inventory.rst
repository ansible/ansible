.. _vmware_ansible_host_inventory:

**********************************************************
Using VMware dynamic inventory plugin for ESXi host system
**********************************************************

.. contents:: Topics

VMware Host Dynamic Inventory Plugin
====================================


The best way to interact with your ESXi hosts is to use the VMware host dynamic inventory plugin, which dynamically queries VMware APIs and
tells Ansible what ESXi nodes can be managed.

To be able to use this VMware host dynamic inventory plugin, you need to enable it first by specifying the following in the ``ansible.cfg`` file:

.. code-block:: ini

  [inventory]
  enable_plugins = vmware_host_inventory

Then, create a file that ends in ``.vmware.yml`` or ``.vmware.yaml`` in your working directory.

The ``vmware_host_inventory`` script takes in the same authentication information as any VMware module.

Here's an example of a valid inventory file:

.. code-block:: yaml

    plugin: vmware_host_inventory
    strict: False
    hostname: 10.65.223.31
    username: administrator@vsphere.local
    password: Esxi@123$%
    validate_certs: False
    with_tags: True
    properties:
        - name
        - summary.hardware.model
        - summary.hardware.vendor
        - summary.hardware.uuid
        - summary.hardware.memorySize
        - summary.hardware.cpuModel
        - summary.hardware.cpuMhz
        - config.product.version


Executing ``ansible-inventory --list -i <filename>.vmware.yml`` will create a list of VMware ESXi host instances that are ready to be used by Ansible.


.. seealso::

    `pyVmomi <https://github.com/vmware/pyvmomi>`_
        The GitHub Page of pyVmomi
    `pyVmomi Issue Tracker <https://github.com/vmware/pyvmomi/issues>`_
        The issue tracker for the pyVmomi project
    :ref:`working_with_playbooks`
        An introduction to playbooks
    :ref:`vmware_ansible_inventory`
        For using VMware guest dynamic inventory use vmware_vm_inventory