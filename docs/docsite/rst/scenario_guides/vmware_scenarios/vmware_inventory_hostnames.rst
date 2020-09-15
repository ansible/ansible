.. _vmware_ansible_inventory_using_hostnames:

*************************************************
Using VMware dynamic inventory plugin - Hostnames
*************************************************

.. contents::
  :local:

VMware dynamic inventory plugin - customizing hostnames
=======================================================


VMware inventory plugin allows you to configure hostnames using the ``hostnames`` configuration parameter.

In this scenario guide we will see how you configure hostnames from the given VMware guest in the inventory.

Requirements
------------

To use the VMware dynamic inventory plugins, you must install `pyVmomi <https://github.com/vmware/pyvmomi>`_
on your control node (the host running Ansible).

To include tag-related information for the virtual machines in your dynamic inventory, you also need the `vSphere Automation SDK <https://code.vmware.com/web/sdk/65/vsphere-automation-python>`_, which supports REST API features such as tagging and content libraries, on your control node.
You can install the ``vSphere Automation SDK`` following `these instructions <https://github.com/vmware/vsphere-automation-sdk-python#installing-required-python-packages>`_.

.. code-block:: bash

    $ pip install pyvmomi

Starting in Ansible 2.10, the VMware dynamic inventory plugin is available in the ``community.vmware`` collection included Ansible.
To install the latest ``community.vmware`` collection:

.. code-block:: bash

    $ ansible-galaxy collection install community.vmware

To use this VMware dynamic inventory plugin:

1. Enable it first by specifying the following in the ``ansible.cfg`` file:

.. code-block:: ini

  [inventory]
  enable_plugins = community.vmware.vmware_vm_inventory

2. Create a file that ends in ``vmware.yml`` or ``vmware.yaml`` in your working directory.

The ``vmware_vm_inventory`` inventory plugin takes in the same authentication information as any other VMware modules does.

Here's an example of a valid inventory file with custom hostname for the given VMware guest:

.. code-block:: yaml

    plugin: community.vmware.vmware_vm_inventory
    strict: False
    hostname: 10.65.223.31
    username: administrator@vsphere.local
    password: Esxi@123$%
    validate_certs: False
    with_tags: False
    hostnames:
    - config.name


Here, we have configured a custom hostname by setting the ``hostnames`` parameter to ``config.name``. This will retrieve
the ``config.name`` property from the virtual machine and populate it in the inventory.

You can check all allowed properties for the given virtual machine at :ref:`vmware_inventory_vm_attributes`.

Executing ``ansible-inventory --list -i <filename>.vmware.yml`` creates a list of the virtual machines that are ready to be configured using Ansible.

What to expect
--------------

You will notice that instead of default behavior of representing the hostname as ``config.name + _ + config.uuid``,
the inventory hosts show value as ``config.name``.


.. code-block:: yaml

    {
      "_meta": {
        "hostvars": {
            "template_001": {
                "config.name": "template_001",
                "guest.toolsRunningStatus": "guestToolsNotRunning",
                ...
                "guest.toolsStatus": "toolsNotInstalled",
                "name": "template_001"
            },
            "vm_8046": {
                "config.name": "vm_8046",
                "guest.toolsRunningStatus": "guestToolsNotRunning",
                ...
                "guest.toolsStatus": "toolsNotInstalled",
                "name": "vm_8046"
            },
        ...
    }

Troubleshooting
---------------

If the custom property specified in ``hostnames`` fails:

- Check if the values provided for username and password are correct.
- Make sure it is a valid property, see :ref:`vmware_inventory_vm_attributes`.
- Use ``strict: True`` to get more information about the error.
- Please make sure that you are using latest version VMware collection.


.. seealso::

    `pyVmomi <https://github.com/vmware/pyvmomi>`_
        The GitHub Page of pyVmomi
    `pyVmomi Issue Tracker <https://github.com/vmware/pyvmomi/issues>`_
        The issue tracker for the pyVmomi project
    `vSphere Automation SDK GitHub Page <https://github.com/vmware/vsphere-automation-sdk-python>`_
        The GitHub Page of vSphere Automation SDK for Python
    `vSphere Automation SDK Issue Tracker <https://github.com/vmware/vsphere-automation-sdk-python/issues>`_
        The issue tracker for vSphere Automation SDK for Python
    :ref:`vmware_inventory_vm_attributes`
        Using Virtual machine attributes in VMware dynamic inventory plugin
    :ref:`working_with_playbooks`
        An introduction to playbooks
    :ref:`playbooks_vault`
        Using Vault in playbooks
