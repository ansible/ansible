******************
Networking Support
******************


.. contents:: Topics

.. _working_with_networking_devices:

Working with Networking Devices
===============================

Starting with Ansible version 2.1, you can now use the familiar Ansible models of playbook authoring and module development to manage heterogeneous networking devices.  Ansible supports a growing number of network devices using both CLI over SSH and API (when available) transports.

.. _networking_installation:

Network Automation Installation
===============================

Ansible comes packaged with networking support. To install Ansible, get the `latest Ansible release <http://docs.ansible.com/ansible/intro_installation.html>`_.

.. _networking_module_index:

Available Networking Modules
=============================

Most standard Ansible modules are designed to work with Linux/Unix or Windows machines and will not work with networking devices. Some modules (including "slurp", "raw", and "setup") are platform-agnostic and will work with networking devices.

To see what modules are available for networking devices, please browse the `"networking" section of the Ansible module index <https://docs.ansible.com/ansible/list_of_network_modules.html#>`_ which are grouped by platform.


What does Ansible Networking look like?
=======================================

TBD Add real work example here

For more examples and how-tos go to LINK




Persistent Connections
======================

As of version 2.3, Ansible includes support for `persistent connections`. Persistent connections are useful for playbooks with multiple tasks that require multiple SSH connections. In previous releases, these SSH connections had to be established and destroyed each time a task was run, which was inefficient. Persistent connections allows an SSH connection to stay active across multiple Ansible tasks and plays, eliminating the need to spend time establishing and destroying the connection. This is done by keeping a Unix socket open, via a daemon process called ``ansible-connection``.

Persistent Connection had been enable for the following groups of modules:

* dellos6
* dellos9
* dellos10
* eos
* ios
* iosxr
* junos
* nxos (some)
* vyos
* sros


.. notes: Future support

   The list of network platforms that support Persistent Connection will grow with each release.

.. notes: Persistent Connections work with the `cli` (ssh) provider, not for API transports.

   The Persistent Connection work added in Ansible 2.3 only applies to the `cli transport`. It doesn't apply to APIs (such as eos's eapi, or nxos's nxapi). Starting with Ansible 2.3, using CLI should be faster in most cases than using the API transport. Using CLI also allows you to benefit from using SSH Keys.

Playbook Structure Changes from 2.1 to 2.3
==========================================

Ansible 2.3 makes it easier to write playbooks by simplifying how connections are handled. This means that you no longer need to define the connection details in every task (via ``host:`` or ``provider:``); instead you can utilize ssh keys and write shortened playbooks.


Ansible 2.3 maintains backwards compatibility with playbooks created in Ansible 2.2, so you are not forced to upgrade your playbooks when you upgrade to Ansible 2.3.

Why is this changing
--------------------

As of Ansible 2.FIXME, specifying credentials directly under the task or under provider will no longer be supported in network modules. This is to make the network modules work in the same way as normal Linux and Windows modules. This has the following advantages:

* Easier to understand
* Consistent with the rest of Ansible
* Simplified module code
* Fewer code paths doing similar things


What a network playbook looks like
-----------------------------------

FIXME Give a real world example here that shows off the power, include full command line


**Version:** Ansible 2.3


.. code-block:: yaml

   - name: Gather facts
     - eos_facts:
         gather_subset: all


For details on how how to pass in authentication details, see `Specifying Credentials`.
See how-tos







# FIXME TOC & link to other pages
