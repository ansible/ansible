.. _RHV_faq:

***************
Ansible RHV FAQ
***************

ovirt_* modules
===============

What is oVirt? What is RHV?
---------------------------

oVirt is the upsteam open-source edition of Red Hat Virtualization. 
Red Hat Virtualization is an open-source alternative hypervisor to such like VMware. As of RHV version 4.1+ the feature-set and 
maturity of RHV insists that it is prime for enterprise production workloads, among others.

What version of oVirt / RHV will Ansible modules work with?
-----------------------------------------------------------

Most of the more recently build ``ovirt_*`` modules are best experienced with oVirt/ RHV 4.1 or newer, hence the preview flags 
on the modules, indicating no guarantee for backwards compatibility.

Can I deploy a virtual machine on a standalone RHV Host server ?
----------------------------------------------------------------

Yes. ``ovirt_vm`` can deploy a virtual machine with required settings on a standalone (local-storage install) RHV Host server.
An arrangement of other ``ovirt_*`` modules combined can achieve more complex VM deployments.

Does oVirt/ RHV have a REST APT?
--------------------------------

Yes, and much of what Ansible can do can be augmented with API calls to the engine.


