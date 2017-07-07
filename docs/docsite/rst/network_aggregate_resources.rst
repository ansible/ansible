*********************************
Aggregate Resources in Networking
*********************************

.. toctree::

This section explores how and when Aggregate Resources can be used within Ansible Networking.



This document is part of a collection on Networking. The complete list of guides can be found at :ref:`Network Guides <guide_networking>`.

Overview
========

Consider the case if you wanted to ensure a set of vlans are present on a switch. Although at a high level thia sounds like a simple request, there in a slight nuance:

* Should these vlans be in *addition* to the existing configuration?  - *additive*
* Should these vlans be the *only* osnes present? - *aggregate*


.. versionadded:: 2.4

   The ``aggregate:`` module options were added in Ansible 2.4 and are only available in certain modules, see the modules documentation to see if the feature is available.

Additive resources
===================

Continuing our vlan example, the following task ensure that vlans ``1``, ``2`` and ``3`` are in the states specified in the task.

This task *will not* change any vlans already configured on the switch.

.. code-block:: yaml

   - name: configure vlans neighbor
     net_vlan:
       vlan_id: “{{ item.vlan_id }}”
       name: “{{ item.name }}”
       state: “{{ item.state | default(‘active’) }}”
     with_items:
       - { vlan_id: 1, name: default }
       - { vlan_id: 2, name: Vl2 }
       - { vlan_id: 3, state: suspend }


The *additive* format can be useful in a number of cases:
* When Ansible isn't your Single Source of truth; and therefore doesn't ...

Aggregate resources
===================



.. code-block:: yaml

   - name: configure vlans neighbor
     net_vlan:
       collection:
         - { vlan_id: 1, name: default }
         - { vlan_id: 2, name: Vl2 }
         - { vlan_id: 3, state: suspend }
       state: active


* purge

  * Default False - WHY
  * What this does
FIXME When you would need this
* WARNING if purge & NOT-aggregate


When would you use aggregate resources?
=======================================


When would you not use aggregate resources?
===========================================


FIXME
=====

* Does a module support ``aggregate:`` - generally only ``net_*``? (is that right)

  * check the module page LINK