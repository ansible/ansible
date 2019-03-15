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

Limiting inventory to a datacenter or folder
============================================

You can limit the search to a specific datacenter or folder. See the example:

.. code-block:: yaml

    plugin: vmware_vm_inventory
    strict: False
    hostname: 10.65.223.31
    username: administrator@vsphere.local
    password: Esxi@123$%
    validate_certs: False
    datacenter: MyDC
    search_folder: Folder1/SubfolderA
    with_tags: True

The ``search_folder`` path is relative to the builtin vm subfolder of the
specified datacenter. So setting ``search_folder`` requires also setting
``datacenter``.

Generating groups from folders
==============================

You can generate ansible groups from vCenter folders with ``with_folders: True``. It requires also setting ``datacenter``.

To keep them unique the group names match the full folder path, replacing
'/' by '_'. As an example, suppose a vCenter folder layout for an AWX lab like
this:

.. code-block:: text

    /AWX
    /AWX/lab
    /AWX/lab/db
    /AWX/lab/workers

Setting ``with_folders: True`` (and a ``datacenter`` name) will generate an inventory like this:

.. code-block:: text

    @all:
      |--@awx:
      |  |--@awx_lab:
      |  |  |--@awx_lab_db:
      |  |  |  |--awx-db01_xxxx-uuid
      |  |  |--@awx_lab_workers:
      |  |  |  |--awx-worker01_xxxx-uuid
      |  |  |  |--awx-worker02_xxxx-uuid
    ...

Also note that even if the ``search_folder`` param is also used specifying an
inner folder, the generated group names still match the full path. So in the
example above if ``search_folder`` was set to *AWX/lab*, the only difference
in the generated groups above would be the absence of the outer *awx* group.

.. seealso::

    `pyVmomi <https://github.com/vmware/pyvmomi>`_
        The GitHub Page of pyVmomi
    `pyVmomi Issue Tracker <https://github.com/vmware/pyvmomi/issues>`_
        The issue tracker for the pyVmomi project
    :ref:`working_with_playbooks`
        An introduction to playbooks
    :ref:`playbooks_vault`
        Using Vault in playbooks
