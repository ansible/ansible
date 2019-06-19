.. _RHV_ansible_intro:

**********************************
Introduction to Ansible for RHV
**********************************

.. contents:: Topics

Introduction
============

Ansible provides various modules to manage RHV infrastructure, which includes datacenter, cluster,
host system and virtual machine.

Requirements
============

Ansible RHV modules often require the ovirt-engine-sdk-python package installed.
You can install ovirt-engine-sdk-python using yum in CentOS or RHEL (pending enabled/ available repositories):

.. code-block:: bash

    $ sudo yum install ovirt-engine-sdk-python


ovirt_* modules
===================

The modules for RHV are all known generally as ``ovirt_<something>``

They are found here: `oVirt Modules <https://docs.ansible.com/ansible/latest/modules/list_of_cloud_modules.html#ovirt>`


.. see also::

    `ovirt-ansible <https://github.com/oVirt/ovirt-ansible>`_
        The GitHub Page for ovirt-ansible roles
    `How to use oVirt Ansible roles <https://ovirt.org/blog/2017/08/ovirt-ansible-roles-how-to-use/>`_
        A blog about oVirt Ansible roles
    :ref:`working_with_playbooks`
        An introduction to playbooks

