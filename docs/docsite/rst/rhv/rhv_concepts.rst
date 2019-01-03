.. _RHV_concepts:

***************************
Ansible for RHV Concepts
***************************

These concepts are common to all uses of Ansible, including RHV automation. 
You need to understand them to use Ansible for RHV automation. 
This basic introduction provides the background you need to follow the 
examples in this guide.

.. contents:: Topics

Control Node
============

Any machine with Ansible installed. You can run commands and playbooks, 
invoking ``/usr/bin/ansible`` or ``/usr/bin/ansible-playbook``, from any 
control node. You can use any computer that has Python installed on it as a 
control node - laptops, shared desktops, and servers can all run Ansible. 
Sorry, but Windows cannot be used as a control node. 
There can be multiple control nodes.

Delegation
==========

If you want to perform a RHV specific task on one host within a RHV Datacenter,
 use the ``delegate_to`` keyword on a task. 
This delegation host will be any host where you have ``pyVmomi`` installed. 
Your control node and ``delegate_to`` host can be same or different.

Modules
=======

These are the units of code Ansible executes. Each module has a particular use,
 from creating virtual machines on RHV/ oVirt to managing clusters within a 
 oVirt/ RHV datacenter. You can invoke a single module with a task, or invoke 
 several different modules in a playbook. For an idea of how many modules 
 Ansible includes, take a look at the 
 :ref:`list of RHV modules<RHV_cloud_modules>`.


Playbooks
=========

The ordered lists of tasks, saved so you can run those tasks in that order
repeatedly and practice infrastructure-as-code. Playbooks can include variables
 as well as tasks. Playbooks are written in YAML and are easy to read, write, 
 share and understand.


ovirt-engine-sdk-python
=======================

Ansible RHV modules often require the ovirt-engine-sdk-python package installed.

You need to install this Python SDK on the host from where you want to invoke RHV automation. For example, if you are using a control 
node then it must be installed on that control node.

If you are using any ``delegate_to`` host which is different from your control node then you need to install the same SDK on that 
``delegate_to`` node.

You can install ovirt-engine-sdk-python using yum in CentOS or RHEL (pending enabled/ available repositories):

.. code-block:: bash

    $ sudo yum install ovirt-engine-sdk-python


