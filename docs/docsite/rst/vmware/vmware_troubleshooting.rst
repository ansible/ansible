.. _vmware_troubleshooting:

**********************************
Troubleshooting Ansible for VMware
**********************************

.. contents:: Topics

This section lists things that can go wrong and possible ways to fix them.

Debugging
=========

When debugging or creating a new issue, you will need information about your VMware infrastructure. You can get this information using
`govc <https://github.com/vmware/govmomi/tree/master/govc>`_, For example:


.. code-block:: bash

    $ export GOVC_USERNAME=ESXI_OR_VCENTER_USERNAME
    $ export GOVC_PASSWORD=ESXI_OR_VCENTER_PASSWORD
    $ export GOVC_URL=https://ESXI_OR_VCENTER_HOSTNAME:443
    $ govc find /


Troubleshooting Item 
====================

Description

Potential Workaround
--------------------

How to fix...