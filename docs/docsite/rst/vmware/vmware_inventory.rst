.. _vmware_ansible_inventory:

*************************************
Using VMware dynamic inventory plugin
*************************************

.. contents:: Topics

VMware Dynamic Inventory Plugin
===============================


The best way to interact with your hosts is to use the VMware dynamic inventory plugin, which dynamically queries VMware APIs and
tells Ansible what nodes can be managed.

To be able to use this VMware dynamic inventory plugin, you need to enable it first by specifying the following in the ``ansible.cfg`` file:

.. code-block:: ini

  [inventory]
  enable_plugins = vmware_vm_inventory

Then, create a file that ends in ``.vmware.yml`` or ``.vmware.yaml`` in your working directory.

The ``vmware_vm_inventory`` script takes in the same authentication information as any VMware module.

Here's an example of a valid inventory file:

.. code-block:: yaml

    plugin: vmware_vm_inventory
    strict: False
    hostname: 10.65.223.31
    username: administrator@vsphere.local
    password: Esxi@123$%
    validate_certs: False
    with_tags: True


Executing ``ansible-inventory --list -i <filename>.vmware.yml`` will create a list of VMware instances that are ready to be configured using Ansible.


.. seealso::

    `pyVmomi <https://github.com/vmware/pyvmomi>`_
        The GitHub Page of pyVmomi
    `pyVmomi Issue Tracker <https://github.com/vmware/pyvmomi/issues>`_
        The issue tracker for the pyVmomi project
    :ref:`working_with_playbooks`
        An introduction to playbooks

