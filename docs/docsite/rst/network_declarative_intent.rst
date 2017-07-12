*********************************
Declarative Intent in Networking
*********************************

.. contents:: Topics

This section explores what `Declarative Intent modules` are within the context of Ansible Networking.

This document is part of a collection on Networking. The complete list of guides can be found at :ref:`Network Guides <guide_networking>`.

Overview
========

Declarative intent modules are designed to provide playbook designers a set of network modules that perform declarative configuration tasks on network devices.  This includes the ability to declaratively describe a configuration set.  In addition, declarative intent modules will also provide a means for declaratively expressing the intended ephemeral state of configuration resources.

**Terms**

* Declarative Configuration
* Intended State
* Declarative intent modules

Declarative intent modules provide playbook designers with the ability to manage individual network device configuration resources in a more intuitive way.  These modules are fundamentally no different that any other module in Ansible core.

Declarative intent modules provide two broad categories of arguments.  The first broad category includes *desired configuration settings*.  These arguments will declaratively perform configuration of the defined resource on the network device.   It does this by first checking the current configuration of the resource and then comparing it with the desired configuration. If there are discrepancies between the current configuration and the desired configuration, the module will automatically take the appropriate steps to bring the two into alignment.

:Intended State:

  Declarative intent modules also provide a set of arguments that allow playbook designers to specify the desired or intended operational state of the resource.  These argument allow tasks to define the normalized operating state of the resource once the configuration has been completed.  **State options do not make configuration changes** to the resource.  They serve to validate that a given resource has normalized its operating environment to reflect the intended state.  If the operating state does not reflect the intended (or desired) state of the resource as described in the playbook task, the module is considered failed and remediation actions can be taken in the playbook during the playbook execution.



.. versionadded:: 2.4

   The `declarative intent modules` are new in Ansible 2.4 and is available in certain modules, see the modules documentation to see if the feature is available.

Without declarative intent
===========================

Enable a port and set vlan

.. code-block:: yaml

   - name: Enable port

Ansible reports everything is OK.

Though if we attempt to talk to the remote system it fails.

The issue here is that we are only asserting *configuration* changes, there is no checks of the *state* of the network infrastructure, for example has the cable been plugged in?

With declaritive intent
=======================

.. code-block:: yaml

   - name: configure interface
     net_interface:
       # Declared configuration
       name: GigabitEthernet0/2
       description: public interface configuration
       enabled: yes

       # Intended state
       state: connected


This above example

Aggregate resources
===================


FIXME
=====

The following need discussing further

* Think about layout and readability
* How to identify intended state options in docs (web or ansible-doc)

  * Marker in in text, colour & link to this page in web?
  * Module examples should have ``# Declared configuration`` and ``# Intended state``

* *configuration* vs *state* vs *physical*?
* ``delay:``

  * is a wait, not a poll
  * Only used when a change is made
* State options do not make configuration changes
  * wait_for is ugly and requires you to know the structure of returned data




* Simplier playbooks (that using ``wait_for``

* Use Cases:
  * Using Ansible to ensure physical connections

    * No point making configuration changes if someone hasn't plugged in the cable - simple case
    * Checking the routing between connection - not just plugged in, but a route exists to the correct location - avoid cabling errors

  * Cabling then configuration
  * Configuration, cabling, check
  * Reminder: Ansible isn't a monitoring tool
  * Block & rescue

    * Roll back configuration?
    * Send (slack) notification that "{{ port }}" isn't configured


























