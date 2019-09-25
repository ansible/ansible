.. _oVirt_faq:

<<<<<<< HEAD
***************
Ansible oVirt FAQ
***************
=======
*****************
Ansible oVirt FAQ
*****************

>>>>>>> b2f160c369d26b7fc5dea65dae33eda7e6686620

ovirt_* modules
===============

<<<<<<< HEAD
What is oVirt? What is oVirt?
---------------------------

oVirt is the upsteam open-source edition of Red Hat Virtualization. 
=======
What is oVirt? What is RHV?
---------------------------

oVirt is the upstream open-source edition of Red Hat Virtualization. 
>>>>>>> b2f160c369d26b7fc5dea65dae33eda7e6686620
Red Hat Virtualization is an open-source alternative hypervisor to such like VMware. As of oVirt version 4.1+ the feature-set and 
maturity of oVirt insists that it is prime for enterprise production workloads, among others.

What version of oVirt/RHV will Ansible modules work with?
-----------------------------------------------------------

Most of the more recently build ``ovirt_*`` modules are best experienced with oVirt/RHV 4.1 or newer, hence the preview flags 
on the modules, indicating no guarantee for backwards compatibility.

Can I deploy a virtual machine on a standalone oVirt Host server ?
<<<<<<< HEAD
----------------------------------------------------------------
=======
-------------------------------------------------------------------
>>>>>>> b2f160c369d26b7fc5dea65dae33eda7e6686620

Yes. ``ovirt_vm`` can deploy a virtual machine with required settings on a standalone (local-storage install) oVirt Host server.
An arrangement of other ``ovirt_*`` modules combined can achieve more complex VM deployments.

Does oVirt/RHV have a REST APT?
--------------------------------

Yes, and much of what Ansible can do can be augmented with API calls to the engine.


