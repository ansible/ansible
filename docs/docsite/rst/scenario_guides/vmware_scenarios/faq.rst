.. _vmware_faq:

******************
Ansible VMware FAQ
******************

vmware_guest
============

Can I deploy a virtual machine on a standalone ESXi server ?
------------------------------------------------------------

Yes. ``vmware_guest`` can deploy a virtual machine with required settings on a standalone ESXi server.


Is ``/vm`` required for ``vmware_guest`` module ?
-------------------------------------------------

Prior to Ansible version 2.5, ``folder`` was an optional parameter with a default value of ``/vm``.

The folder parameter was used to discover information about virtual machines in the given infrastructure.

Starting with Ansible version 2.5, ``folder`` is still an optional parameter with no default value.
This parameter will be now used to identify a user's virtual machine, if multiple virtual machines or virtual
machine templates are found with same name. VMware does not restrict the system administrator from creating virtual
machines with same name.
