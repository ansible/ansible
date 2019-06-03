.. _vmware_ansible_inventory:

*************************************
Using VMware dynamic inventory plugin
*************************************

.. contents:: Topics

VMware Dynamic Inventory Plugin
===============================


The best way to interact with your hosts is to use the VMware dynamic inventory plugin, which dynamically queries VMware APIs and
tells Ansible what nodes can be managed.

Requirements
------------

To use the VMware dynamic inventory plugins, you must install `pyVmomi <https://github.com/vmware/pyvmomi>`_
on your control node (the host running Ansible).

To include tag-related information for the virtual machines in your dynamic inventory, you also need the `vSphere Automation SDK <https://code.vmware.com/web/sdk/65/vsphere-automation-python>`_, which supports REST API features like tagging and content libraries, on your control node.
You can install the ``vSphere Automation SDK`` following `these instructions <https://github.com/vmware/vsphere-automation-sdk-python#installing-required-python-packages>`_.

.. code-block:: bash

    $ pip install pyvmomi

To use this VMware dynamic inventory plugin, you need to enable it first by specifying the following in the ``ansible.cfg`` file:

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

Using vaulted configuration files
=================================

Since the inventory configuration file contains vCenter password in plain text, a security risk, you may want to
encrypt your entire inventory configuration file.

You can encrypt a valid inventory configuration file as follows:

.. code-block:: bash

    $ ansible-vault encrypt <filename>.vmware.yml
      New Vault password:
      Confirm New Vault password:
      Encryption successful

And you can use this vaulted inventory configuration file using:

.. code-block:: bash

    $ ansible-inventory -i filename.vmware.yml --list --vault-password-file=/path/to/vault_password_file


.. seealso::

    `pyVmomi <https://github.com/vmware/pyvmomi>`_
        The GitHub Page of pyVmomi
    `pyVmomi Issue Tracker <https://github.com/vmware/pyvmomi/issues>`_
        The issue tracker for the pyVmomi project
    `vSphere Automation SDK GitHub Page <https://github.com/vmware/vsphere-automation-sdk-python>`_
        The GitHub Page of vSphere Automation SDK for Python
    `vSphere Automation SDK Issue Tracker <https://github.com/vmware/vsphere-automation-sdk-python/issues>`_
        The issue tracker for vSphere Automation SDK for Python
    :ref:`working_with_playbooks`
        An introduction to playbooks
    :ref:`playbooks_vault`
        Using Vault in playbooks
