.. _vmware_concepts:

***************************
Ansible for VMware Concepts
***************************

These concepts are common to all uses of Ansible, including VMware automation. You need to understand them to use Ansible for VMware automation. This basic introduction provides the background you need to follow the examples in this guide.

.. contents:: Topics

Control Node
============

Any machine with Ansible installed. You can run commands and playbooks, invoking ``/usr/bin/ansible`` or ``/usr/bin/ansible-playbook``, from any control node. You can use any computer that has Python installed on it as a control node - laptops, shared desktops, and servers can all run Ansible. However, you cannot use a Windows machine as a control node. You can have multiple control nodes.

Delegation
==========

If you want to perform a VMware specific task on one host with reference to ESXi server or vCenter server, use the ``delegate_to`` keyword on a task. This delegation host will be any host where you have ``pyVmomi`` installed. Your control node and ``delegate_to`` host can be same or different.

Modules
=======

The units of code Ansible executes. Each module has a particular use, from creating virtual machines on vCenter to managing distributed virtual switches on vCenter environment. You can invoke a single module with a task, or invoke several different modules in a playbook. For an idea of how many modules Ansible includes, take a look at the :ref:`list of VMware modules<vmware_cloud_modules>`.


Playbooks
=========

Ordered lists of tasks, saved so you can run those tasks in that order repeatedly. Playbooks can include variables as well as tasks. Playbooks are written in YAML and are easy to read, write, share and understand.


pyVmomi
=======

Ansible VMware modules are written on top of `pyVmomi <https://github.com/vmware/pyvmomi>`_. ``pyVmomi`` is the official Python SDK for the VMware vSphere API that allows user to manage ESX, ESXi, and vCenter infrastructure.

You need to install this Python SDK on host from where you want to invoke VMware automation. For example, if you are using control node then ``pyVmomi`` must be installed on control node.

If you are using any ``delegate_to`` host which is different from your control node then you need to install ``pyVmomi`` on that ``delegate_to`` node.

You can install pyVmomi using pip:

.. code-block:: bash

    $ pip install pyvmomi
