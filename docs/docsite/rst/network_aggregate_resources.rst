*********************************
Aggregate Resources in Networking
*********************************

.. contents:: Topics

This section explores how and when `Aggregate Resources` can be used within Ansible Networking.

This document is part of a collection on Networking. The complete list of guides can be found at :ref:`Network Guides <guide_networking>`.

Overview
========

Consider the case if you wanted to ensure a set of vlans are present on a switch. Although at a high level this sounds like a simple request, there in a slight nuance:

* Should these vlans be in *addition* to the existing configuration?  - *additive*
* Should these vlans be the *only* ones present? - *aggregate*


.. versionadded:: 2.4

   The ``aggregate:`` option has been added in Ansible 2.4 and is available in certain modules, see the modules documentation to see if the feature is available.

Additive resources
===================

Continuing our vlan example, the following task ensure that vlans ``1``, ``2`` and ``3`` are in the states specified in the task, in `addition` to any existing vlans.

This task *will not* change any vlans already configured on the switch, apart from the ones specified in the task.

.. code-block:: yaml

   - name: configure vlans neighbor in addition to existing
     net_vlan:
       vlan_id: “{{ item.vlan_id }}”
       name: “{{ item.name }}”
       state: “{{ item.state | default(‘active’) }}”
     with_items:
       - { vlan_id: 1, name: default }
       - { vlan_id: 2, name: mgmt }
       - { vlan_id: 3, state: suspend }


Aggregate resources
===================

Consider the following example:

.. code-block:: yaml

   - name: configure vlans neighbor (delete others)
     net_vlan:
       aggregate:
         - { vlan_id: 1, name: default }
         - { vlan_id: 2, name: mgmt }
         - { vlan_id: 3, state: suspend }
       state: active
       purge: yes

This task is very similar to the `additive resource` example above, though with the following differences:

* The ``purge:`` option (which defaults to `no`) ensure that **only** the specified entries are present. All other entries will be **deleted**.

.. note:: Why does ``purge`` default to ``no``?

   To prevent from accidental deletion ``purge`` is always set to ``no``. This requires playbook writers to add ``purge: yes`` to enable this.



When would you use aggregate resources?
=======================================

* Ansible is your "Source of Truth"
* FIXME
* Security


When would you not use aggregate resources?
===========================================


The *additive* format can be useful in a number of cases:
* When Ansible isn't your Single Source of truth; and therefore doesn't ...
* FIXME

FIXME
=====

The following need discussing further

* Should we warn if purge & not aggregate

  * Do we want to add ``required_if = [('purge', 'true', ['aggregate'])]``
* Does the order matter
* Link to `Aggreate declaritive intent`
