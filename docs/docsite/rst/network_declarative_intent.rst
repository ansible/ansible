*********************************
Declarative Intent in Networking
*********************************

.. contents:: Topics

This section explores what `Declarative Intent modules` are within the context of Ansible Networking.

This document is part of a collection on Networking. The complete list of guides can be found at :ref:`Network Guides <guide_networking>`.

Overview
========

INTERNAL NOTE: TBD - Short description of the problem. Needs to be very simple

State what you want the end result to be, not how go get there
This results in easier to understand playbooks, which internally deal with the differences between Network OS versions.


Reminder: Ansible isn't a monitoring tool.



Without declarative intent
==========================

INTERNAL NOTE: TBD - Simplist case that shows the issue. We can build on this later

Enable a port and set vlan

.. code-block:: yaml

   - name: Enable port

Ansible reports everything is OK.

The issue here is that we are only asserting *configuration* changes, there is no checks of the *state* of the network infrastructure, for example has the cable been plugged in?


With declaritive intent
=======================

INTERNAL NOTE: TBD - Simplist case that shows the solution. We can build on this later

.. code-block:: yaml

   - name: configure interface
     net_interface:
       # Declared configuration
       name: GigabitEthernet0/2
       description: public interface configuration
       enabled: yes

       # Intended state
       state: connected




Declarative intent - the details
================================

INTERNAL NOTE: Only now that we've explained the problem and given an example should we go into details.


Declarative intent modules are designed to provide playbook designers a set of network modules that perform declarative configuration tasks on network devices.  This includes the ability to declaratively describe a configuration set.  In addition, declarative intent modules will also provide a means for declaratively expressing the intended ephemeral state of configuration resources.


Declarative intent modules provide playbook designers with the ability to manage individual network device configuration resources in a more intuitive way.  These modules are fundamentally no different that any other module in Ansible core.

**Declarative intent modules**

Declarative intent modules, new in Ansible 2.4, take two broad categories of options:

* The first broad category includes *desired configuration settings*.  These options will declaratively perform configuration of the defined resource on the network device.   It does this by first checking the current configuration of the resource and then comparing it with the desired configuration. If there are discrepancies between the current configuration and the desired configuration, the module will automatically take the appropriate steps to bring the two into alignment.
* The second is *intended state* which allows the playbook designer to specifiy the desired state


**Declarative Configuration**

TBD

**Intended State**

Declarative intent modules also take a set of options that allow playbook designers to specify the desired or intended operational state of the resource.  These options allow tasks to define the normalized operating state of the resource once the configuration has been completed.  **State options do not make configuration changes** to the resource.  They serve to validate that a given resource has normalized its operating environment to reflect the intended state.  If the operating state does not reflect the intended (or desired) state of the resource as described in the playbook task, the module is considered failed and remediation actions can be taken in the playbook during the playbook execution.



.. versionadded:: 2.4

   The `declarative intent modules` are new in Ansible 2.4 and is available in certain modules, see the modules documentation to see if the feature is available.

Use cases
==========

Replacing ``wait_for``
---------------------

**Before:**


.. code-block:: yaml

   - name: configure interface

**After:**


.. code-block:: yaml

   - name: configure interface


**Advantages**

* Cleaner playbooks
* Easier to write
* Q: Why else

Q: Any disadvantages?
* not all modules support declaritive_intent - raise an issue


Physical then configuration
---------------------------

**Overview**

* No point making configuration changes if someone hasn't plugged in the cable - simple case
  * Checking the routing between connection - not just plugged in, but a route exists to the correct location - avoid cabling errors

.. code-block:: yaml

   - name: FIXME

**When would this be useful**

*

**When would this not be useful**

*

Configuration then physical
---------------------------

Q: What would this look like

**Overview**


.. code-block:: yaml

   - name: FIXME

**When would this be useful**

*

**When would this not be useful**

*

Checking state only
-------------------
Q: What would this look like

**Overview**


.. code-block:: yaml

   - name: FIXME

**When would this be useful**

*

**When would this not be useful**

*

Configuration, cabling, check
Q: What would this look like

**Overview**


.. code-block:: yaml

   - name: FIXME

**When would this be useful**

*

**When would this not be useful**

*


Rolling back: dealing with failure
----------------------------------

Block & Rescue

* Roll back configuration?
* Send (slack) notification that "{{ port }}" isn't configured, check cabling

Q: What would this look like

**Overview**


.. code-block:: yaml

   - name: FIXME

**When would this be useful**

*

**When would this not be useful**

*

Implementation details
======================

``delay:`` option
-----------------

 ``delay:``

* Why this option exists
* is a wait, not a poll
* When you might need to change the value - How might you tell
* Only used when a change is made, therefore second runs are quicker

If configuration fails
------------------------

* task with config & state - If config fails we never look at state, we will instantly fail. 



FIXME
=====

* Think about layout and readability


Content
-------

* How to identify intended state options in docs (web or ansible-doc)

  * Marker in in text, colour & link to this page in web?
  * Module examples should have ``# Declared configuration`` and ``# Intended state``

* *configuration* vs *state* vs *physical*?
* ``delay:``
* State options do not make configuration changes
  * wait_for is ugly and requires you to know the structure of returned data



* Simplier playbooks (that using ``wait_for``)

* Use Cases:
  * Reminder: Ansible isn't a monitoring tool
  * task with config & state - If config fails we never look at state, we will instantly fail.
  * Can be used without config just to check state


Module index
-------------

TOC
Cisco ASA
Cisco IOS
..
Arista EOS
Platform agnostic layer 2
Platform agnostic layer 2























