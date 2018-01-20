Getting Started with VMware
===========================

Introduction
````````````

Ansible provides various modules to manage VMware infrastructure which includes datacenter, cluster,
host system and virtual machine etc.

Requirements
````````````

Ansible VMware modules are written on top of `pyVmomi <https://github.com/vmware/pyvmomi>`_.
pyVmomi is the Python SDK for the VMware vSphere API that allows user to manage ESX, ESXi,
and vCenter infrastcture. User can install pyVmomi using

.. code-block:: bash

    $ pip install pyvmomi


vmware_guest module
```````````````````

The ``vmware_guest`` module is used to manage various operations related to virtual machines in
the given ESXi or vCenter server.

Prior to Ansible version 2.5, ``folder`` was an optional parameter with value as ``/vm``. Folder parameter
 was used to find about virtual machine in the given infrastructure.

From Ansible version 2.5 and onwards, ``folder`` is still an optional parameter with no default value.
This parameter will be now used to identify user desired virtual machine, if multiple virtual machines or virtual
machine templates are found with same name. VMware does not restrict system administrator from creating virtual
machine with same name.

Debugging
`````````

In order to understand the issue related to VMware modules, one must understand infrastucture details. So, while
create a new issue, please provide information about user VMware infrastructure. User can get this information using
`govc <https://github.com/vmware/govmomi/tree/master/govc>`_ like -


.. code-block:: bash

    $ export GOVC_USERNAME=<ESXI_OR_VCENTER_USERNAME>
    $ export GOVC_PASSWORD=<ESXI_OR_VCENTER_PASSWORD>
    $ export GOVC_URL=https://<ESXI_OR_VCENTER_HOSTNAME>:443
    $ govc find /


.. seealso::

    `pyVmomi <https://github.com/vmware/pyvmomi>`_
        The GitHub Page of pyVmomi
    `pyVmomi Issue Tracker <https://github.com/vmware/pyvmomi/issues>`_
        The issue tracker for the pyVmomi project
    `govc <https://github.com/vmware/govmomi/tree/master/govc>`_
        govc is a vSphere CLI built on top of govmomi.
    :doc:`playbooks`
        An introduction to playbooks

