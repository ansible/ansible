*********************************
Declarative intent in networking
*********************************

.. contents:: Topics

This section explores what `declarative intent modules` are within the context of Ansible networking.

This document is part of a collection on networking. The complete list of guides can be found at :ref:`network guides <guide_networking>`.

Overview
========

INTERNAL NOTE: TBD - Short description of the problem. Needs to be very simple

State what you want the end result to be, not how go get there
This results in easier to understand playbooks, which internally deal with the differences between network OS versions.


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

INTERNAL NOTE: TBD - Simplist case that shows the solution. We can build out the example in the later use-cases.

**Simple example**

.. code-block:: yaml

   - name: configure interface
     net_interface:
       # Declared configuration
       name: GigabitEthernet0/2
       description: public interface configuration
       enabled: yes

       # Intended state
       state: connected

**Complex example**

.. code-block:: yaml

   - name: configure interface
     net_interface:
       # Declared configuration
       description: public interface configuration
       enabled: yes
       aggregate:
         - { name: GigabitEthernet0/2 }
         - { name: GigabitEthernet0/3 }
         - { name: GigabitEthernet0/4 }

       # Intended state
       state: connected
       txrate: 10gb

FIXME: Check syntax



Declarative intent - the details
================================

INTERNAL NOTE: Only now that we've explained the problem and given an example should we go into details.


Previous network modules allowed users to update a device by listing out the steps that need to be taking in order to achieve a desired state. Declarative intent modules are designed to provide playbook designers a set of network modules that perform declarative configuration tasks on network devices.  This includes the ability to declaratively describe a configuration set.  In addition, declarative intent modules will also provide a means for declaratively expressing the intended ephemeral state of configuration resources.


Declarative intent modules provide playbook designers with the ability to manage individual network device configuration resources in a more intuitive way.  These modules are fundamentally no different that any other module in Ansible core.

**Declarative intent modules**

Declarative intent modules, new in Ansible 2.4, take two broad categories of options:

* The first broad category includes *desired configuration settings*.  These options will declaratively perform configuration of the defined resource on the network device.   It does this by first checking the current configuration of the resource and then comparing it with the desired configuration. If there are discrepancies between the current configuration and the desired configuration, the module will automatically take the appropriate steps to bring the two into alignment.
* The second is *intended state* which allows the playbook designer to specifiy the desired state


**Declarative configuration**

FIXME: TBD

**Intended state**

Declarative intent modules also take a set of options that allow playbook designers to specify the desired or intended operational state of the resource.  These options allow tasks to define the normalized operating state of the resource once the configuration has been completed.  **State options do not make configuration changes** to the resource.  They serve to validate that a given resource has normalized its operating environment to reflect the intended state.  If the operating state does not reflect the intended (or desired) state of the resource as described in the playbook task, the module is considered failed and remediation actions can be taken in the playbook during the playbook execution.


.. versionadded:: 2.4

The `declarative intent modules` are new in Ansible 2.4 and is available in certain modules, see the modules documentation to see if the feature is available.

Use cases
==========

Replacing ``wait_for``
----------------------

**Before:**


.. code-block:: yaml

   - name: configure interface

FIXME: Example

**After:**


.. code-block:: yaml

   - name: configure interface
     net_interface:
       # Declared configuration
       name: GigabitEthernet0/2
       description: public interface configuration
       enabled: yes

       # Intended state
       state: connected


**Advantages**

* As you can tell from the above example using the declaritive intent format results in a much cleaner task. Checking no longer required the clunky (find better term) ``wait_for``.
* FIXME: TBD: Add details of why it's better to use the module from an internal code point of view
* Can be combined with ``aggregate:`` to easily ensure state across multiple items.
* FIXME: Q: Why else

FIXME: Q: Any disadvantages?

* not all modules support declaritive_intent - raise an feature request LINK


Physical then configuration
---------------------------

**Overview**

* No point making configuration changes if someone hasn't plugged in the cable - simple case

  * Checking the routing between connection - not just plugged in, but a route exists to the correct location - avoid cabling errors

.. code-block:: yaml

   - name: FIXME

FIXME: Example

**When would this be useful**

* fixme

**When would this not be useful**

* fixme

Configuration then physical
---------------------------

FIXME: Q: What would this look like

**Overview**


.. code-block:: yaml

   - name: FIXME

**When would this be useful**

* Physical then configuration

**When would this not be useful**



Checking state only
-------------------

FIXME: Q: What would this look like

**Overview**


.. code-block:: yaml

   - name: FIXME

**When would this be useful**

* fixme

**When would this not be useful**

* fixme

Configuration, cabling, check
-----------------------------

FIXME: Q: What would this look like

**Overview**


.. code-block:: yaml

   - name: FIXME

**When would this be useful**

* fixme

**When would this not be useful**

* fixme

Aggreate declaritive intent
---------------------------

FIXME: Q: What would this look like

**Overview**


.. code-block:: yaml

   - name: FIXME

**When would this be useful**

* fixme

**When would this not be useful**

* fixme

Link to network_aggregate_resources for more info

Rolling back: dealing with failure
----------------------------------

Block & Rescue

* Roll back configuration?
* Send (slack) notification that "{{ port }}" isn't configured, check cabling

FIXME: Q: What would this look like

**Overview**


.. code-block:: yaml

   - name: FIXME

**When would this be useful**

* fixme

**When would this not be useful**

* fixme

Implementation details
======================

The ``delay:`` option
----------------------

All declaritive intent modules support a ``delay:`` option. This represents the amount of time, in seconds, that Ansible will wait after setting declaritive configuration before checking the indended state. This pause is needed to allow the network device being configured to stablise, such as to allow handshake after bring up an interface.


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
  * Care needed with `state:` `state: present` vs `state: up`

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






