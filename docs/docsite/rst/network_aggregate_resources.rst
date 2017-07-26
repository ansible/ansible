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

This task *will not* change any vlans already configured on the switch, apart from the ones specified in the task. Ansible will ensure that the vlans specified in the task exist with the `name` and `state` specified.

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

FIXME Should we even document ``with_items``, is that just confusing the matter. Should this be the same as `Aggregate resources` though without ``purge: yes``?

FIXME Only showing ``with_items`` to show how it could be done


Would be better written as

.. code-block:: yaml

   - name: configure vlans neighbor (delete others)
     net_vlan:
       aggregate:
         - { vlan_id: 1, name: default }
         - { vlan_id: 2, name: mgmt }
         - { vlan_id: 3, state: suspend }
       state: active

This task is very similar to the `additive resource` example above, though with the following differences:

* The module runs only once, rather than n times as it does ``with_items``
* There is no way to to use ``purge`` on ``with_items``


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
       purge: yes # Important

FIXME Descrbe ``purge``
* The ``purge:`` option (which defaults to `no`) ensures that **only** the specified entries are present. All other entries will be **deleted**.


FIXME: the ``state:`` is Local overrides of global module values

.. warning:: Why does ``purge`` default to ``no``?

   To prevent from accidental deletion ``purge`` is always set to ``no``. This requires playbook writers to add ``purge: yes`` to enable this.



Local overrides of global module values
=======================================

* What
* Why: Cleaner short hand. Allows you to separate out what's common from what's item specific.

.. code-block:: yaml

   - name: configure vlans neighbor (delete others)
     net_vlan:
       aggregate:
         - { vlan_id: 4 }
         - { vlan_id: 5, name: mgmt }
         - { vlan_id: 6 }
       name: reserved_vlan
       state: active # override
       purge: yes # override

Become realy power on ``net_interfaces``, mtu, admin_state, description
Even more so on ``bpg_neighbour``: https://github.com/ansible/ansible/blob/devel/lib/ansible/modules/network/nxos/nxos_bgp_neighbor_af.py#L655


Reference ID shorthand
======================


.. code-block:: yaml

   - name: configure vlans neighbor (delete others)
     net_vlan:
       aggregate:
         - 1
         - 2
         - 3
       state: active
       name: reserved_vlan
       purge: yes


.. code-block:: yaml

   - name: configure vlans neighbor (delete others)
     net_vlan:
       aggregate:
         - 4
         - { vlan_id: 5, name: mgmt }
         - 6
       name: reserved_vlan
       state: active
       purge: yes


When would you use aggregate resources with ``purge: true``?
============================================================

* Ansible to execute your "single source of truth" (execute here means we can talk to source  of truth, e.g. CMS or external data source)
* Ansible is your "Source of Truth"


When would you aggregate resources with ``purge: false``?
=========================================================


The *additive* format can be useful in a number of cases:

* When Ansible isn't executing your Single Source of truth; and therefore doesn't ...
* Allows you to start using Ansible to configure just one part of your network
* FIXME

FIXME
=====

The following need discussing further

* Should we warn if purge & not aggregate

  * Do we want to add ``required_if = [('purge', 'true', ['aggregate'])]``
  * Maybe no, as we may want to factory reset a all vlans
  * Add tests for this
* Does the order matter
* Link to `Aggreate declaritive intent`
* Docs marker for "Reference ID"