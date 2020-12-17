.. _vmware_ansible_inventory_using_filters:

***********************************************
Using VMware dynamic inventory plugin - Filters
***********************************************

.. contents::
  :local:

VMware dynamic inventory plugin - filtering VMware guests
=========================================================


VMware inventory plugin allows you to filter VMware guests using the ``filters`` configuration parameter.

This section shows how you configure ``filters`` for the given VMware guest in the inventory.

Requirements
------------

To use the VMware dynamic inventory plugins, you must install `pyVmomi <https://github.com/vmware/pyvmomi>`_
on your control node (the host running Ansible).

To include tag-related information for the virtual machines in your dynamic inventory, you also need the `vSphere Automation SDK <https://code.vmware.com/web/sdk/65/vsphere-automation-python>`_, which supports REST API features such as tagging and content libraries, on your control node.
You can install the ``vSphere Automation SDK`` following `these instructions <https://github.com/vmware/vsphere-automation-sdk-python#installing-required-python-packages>`_.

.. code-block:: bash

    $ pip install pyvmomi

Starting in Ansible 2.10, the VMware dynamic inventory plugin is available in the ``community.vmware`` collection included Ansible.
Alternately, to install the latest ``community.vmware`` collection:

.. code-block:: bash

    $ ansible-galaxy collection install community.vmware

To use this VMware dynamic inventory plugin:

1. Enable it first by specifying the following in the ``ansible.cfg`` file:

.. code-block:: ini

  [inventory]
  enable_plugins = community.vmware.vmware_vm_inventory

2. Create a file that ends in ``vmware.yml`` or ``vmware.yaml`` in your working directory.

The ``vmware_vm_inventory`` inventory plugin takes in the same authentication information as any other VMware modules does.

Let us assume we want to list all RHEL7 VMs with the power state as "poweredOn". A valid inventory file with filters for the given VMware guest looks as follows:

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
    filters:
    - config.guestId == "rhel7_64Guest"
    - summary.runtime.powerState == "poweredOn"


Here, we have configured two filters -

* ``config.guestId`` is equal to ``rhel7_64Guest``
* ``summary.runtime.powerState`` is equal to ``poweredOn``

This retrieves all the VMs which satisfy these two conditions and populates them in the inventory.
Notice that the conditions are combined using an ``and`` operation.

Using ``or`` conditions in filters
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Let us assume you want filter RHEL7 and Ubuntu VMs. You can use multiple filters using ``or`` condition in your inventory file.

A valid filter in the VMware inventory file for this example is:

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
    filters:
    - config.guestId == "rhel7_64Guest" or config.guestId == "ubuntu64Guest"


You can check all allowed properties for filters for the given virtual machine at :ref:`vmware_inventory_vm_attributes`.

If you are using the ``properties`` parameter with custom VM properties, make sure that you include all the properties used by filters as well in your VM property list.

For example, if we want all RHEL7 and Ubuntu VMs that are poweredOn, you can use inventory file:

.. code-block:: yaml

    plugin: community.vmware.vmware_vm_inventory
    strict: False
    hostname: 10.65.223.31
    username: administrator@vsphere.local
    password: Esxi@123$%
    validate_certs: False
    with_tags: False
    hostnames:
    - 'config.name'
    properties:
    - 'config.name'
    - 'config.guestId'
    - 'guest.ipAddress'
    - 'summary.runtime.powerState'
    filters:
    - config.guestId == "rhel7_64Guest" or config.guestId == "ubuntu64Guest"
    - summary.runtime.powerState == "poweredOn"

Here, we are using minimum VM properties, that is ``config.name``, ``config.guestId``, ``summary.runtime.powerState``, and ``guest.ipAddress``.

* ``config.name`` is used by the ``hostnames`` parameter.
* ``config.guestId`` and ``summary.runtime.powerState`` are used by the ``filters`` parameter.
* ``guest.guestId`` is used by ``ansible_host`` internally by the inventory plugin.

Using regular expression in filters
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Let us assume you want filter VMs with specific IP range. You can use regular expression in ``filters`` in your inventory file.

For example, if we want all RHEL7 and Ubuntu VMs that are poweredOn, you can use inventory file:

.. code-block:: yaml

    plugin: community.vmware.vmware_vm_inventory
    strict: False
    hostname: 10.65.223.31
    username: administrator@vsphere.local
    password: Esxi@123$%
    validate_certs: False
    with_tags: False
    hostnames:
    - 'config.name'
    properties:
    - 'config.name'
    - 'config.guestId'
    - 'guest.ipAddress'
    - 'summary.runtime.powerState'
    filters:
    - guest.ipAddress is defined and guest.ipAddress is match('192.168.*')

Here, we are using ``guest.ipAddress`` VM property. This property is optional and depended upon VMware tools installed on VMs.
We are using ``match`` to validate the regular expression for the given IP range.

Executing ``ansible-inventory --list -i <filename>.vmware.yml`` creates a list of the virtual machines that are ready to be configured using Ansible.

What to expect
--------------

You will notice that the inventory hosts are filtered depending on your ``filters`` section.


.. code-block:: yaml

    {
      "_meta": {
        "hostvars": {
            "template_001": {
                "config.name": "template_001",
                "config.guestId": "ubuntu64Guest",
                ...
                "guest.toolsStatus": "toolsNotInstalled",
                "summary.runtime.powerState": "poweredOn",
            },
            "vm_8046": {
                "config.name": "vm_8046",
                "config.guestId": "rhel7_64Guest",
                ...
                "guest.toolsStatus": "toolsNotInstalled",
                "summary.runtime.powerState": "poweredOn",
            },
        ...
    }

Troubleshooting filters
-----------------------

If the custom property specified in ``filters`` fails:

- Check if the values provided for username and password are correct.
- Make sure it is a valid property, see :ref:`vmware_inventory_vm_attributes`.
- Use ``strict: True`` to get more information about the error.
- Please make sure that you are using latest version of the VMware collection.


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
