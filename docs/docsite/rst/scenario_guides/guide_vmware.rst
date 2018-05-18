Getting Started with VMware
===========================

Introduction
````````````

Ansible provides various modules to manage VMware infrastructure, which includes datacenter, cluster,
host system and virtual machine.

Requirements
````````````

Ansible VMware modules are written on top of `pyVmomi <https://github.com/vmware/pyvmomi>`_.
pyVmomi is the Python SDK for the VMware vSphere API that allows user to manage ESX, ESXi,
and vCenter infrastcture. You can install pyVmomi using pip:

.. code-block:: bash

    $ pip install pyvmomi


vmware_guest module
```````````````````

The :ref:vmware_guest <vmware_guest>module is used to manage various operations related to virtual machines in
the given ESXi or vCenter server.

Prior to Ansible version 2.5, ``folder`` was an optional parameter with a default value of ``/vm``. The folder parameter
 was used to discover information about virtual machines in the given infrastructure.

Starting with Ansible version 2.5, ``folder`` is still an optional parameter with no default value.
This parameter will be now used to identify a user's virtual machine, if multiple virtual machines or virtual
machine templates are found with same name. VMware does not restrict the system administrator from creating virtual
machines with same name.

Debugging
`````````
When debugging or creating a new issue, you will need information about your VMware infrastructure. You can get this information using
`govc <https://github.com/vmware/govmomi/tree/master/govc>`_, For example:


.. code-block:: bash

    $ export GOVC_USERNAME=ESXI_OR_VCENTER_USERNAME
    $ export GOVC_PASSWORD=ESXI_OR_VCENTER_PASSWORD
    $ export GOVC_URL=https://ESXI_OR_VCENTER_HOSTNAME:443
    $ govc find /


.. seealso::

    `pyVmomi <https://github.com/vmware/pyvmomi>`_
        The GitHub Page of pyVmomi
    `pyVmomi Issue Tracker <https://github.com/vmware/pyvmomi/issues>`_
        The issue tracker for the pyVmomi project
    `govc <https://github.com/vmware/govmomi/tree/master/govc>`_
        govc is a vSphere CLI built on top of govmomi
    :ref:`working_with_playbooks`
        An introduction to playbooks

