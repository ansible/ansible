*********************************
Aggregate resources in networking
*********************************

.. contents:: Topics

This section explores how and when `aggregate resources` can be used within Ansible networking.

This document is part of a collection on networking. The complete list of guides can be found at :ref:`network guides <guide_networking>`.

Overview
========

Consider the case if you wanted to ensure a set of vlans are present on a switch. Although at a high level this sounds like a simple request, there in a slight nuance:

* If the vlans are to be in *addition* to the existing configuration, they are considered **additive** vlans.
* If the vlans are the *only* ones to exist, they are considered **aggregate** vlans.


.. versionadded:: 2.4

The ``aggregate:`` option has been added in Ansible 2.4 and is available in certain modules. See the modules documentation to see if the feature is available.

Additive resources
===================

Continuing our vlan example, the following task ensures that vlans ``1``, ``2`` and ``3`` are in the states specified in the task, in `addition` to any existing vlans.

This task *will not* change any vlans already configured on the switch, apart from the ones specified in the task. Ansible will ensure that the vlans specified in the task exist with the `name` and `state` specified.

**Bad**

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

The above task is executed 3 times (once per ``item``), this is very inefficient and will take a considerable time to execute as a seperate connection is made to the network device for each ``item``.


**Better format**

The preceding example would be better written as follows:

.. code-block:: yaml

   - name: configure vlans, and delete others
     net_vlan:
       aggregate:
         - { vlan_id: 1, name: default }
         - { vlan_id: 2, name: mgmt }
         - { vlan_id: 3, state: suspend }
       state: active

This task is very similar to the *additive resource* example above, though with the following differences:

* The module (``net_vlan``) is executed only **once**, rather than *n* times as it does ``with_items``
* There is no way to to use ``purge`` on ``with_items``, more on that in the `aggregate resources` section.
* Easier to write a cleaner task


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

The ``state:`` is "local overrides of global module values", see FIXMELINK: Local overrides of global module values.


Purge
=====

* The ``purge:`` option (which defaults to `no`) ensures that **only** the specified entries are present. All other entries will be **deleted**.


.. warning:: Why does ``purge`` default to ``no``?

To prevent from accidental deletion, ``purge`` is always set to ``no``. This requires playbook writers to add ``purge: yes`` to enable this, i.e. opt-in to potentially dangerious behaviour.

When would you use aggregate resources with ``purge: true``?
------------------------------------------------------------

* Ansible to execute your "single source of truth" (execute here means we can talk to source  of truth, e.g. CMS or external data source)
* Ansible is your "Source of Truth"


When would you aggregate resources with ``purge: false``?
---------------------------------------------------------


The *additive* format can be useful in a number of cases:

* When Ansible isn't executing your Single Source of truth; and therefore doesn't ...
* Allows you to start using Ansible to configure just one part of your network
* FIXME


Local overrides of global module values
=======================================

When writing tasks using ``aggregate`` you may find yourself repeating various settings within the aggregate dictionary, for example:

.. code-block:: yaml

   - name: Reserve mgmt vlans
     net_vlan:
       aggregate:
         - { vlan_id: 4, name: reserved_vlan, state: active }
         - { vlan_id: 5, name: mgmt, state: active }
         - { vlan_id: 6, name: reserved_vlan , state: active}
       name: reserved_vlan
       state: active # override

In the above example we can see that ``state: active`` is set for all vlans, and most have ``name: reserved_vlan``. We can simplify this to:


.. code-block:: yaml

   - name: Reserve mgmt vlans
     net_vlan:
       aggregate:
         - { vlan_id: 4 }
         - { vlan_id: 5, name: mgmt }
         - { vlan_id: 6 }
       name: reserved_vlan # override
       state: active # override


Note that:

* Shorter task
* The special cases, ``name: mgmt``, stand out a lot more, increasing readability
* This can be very powerful when a module uses take a lot of options, most of which are common, such as ``net_interfaces`` or ``nxos_bgp_neighbor_af``

FIXME: Become realy power on ``net_interfaces``, mtu, admin_state, description


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




FIXME
=====

The following need discussing further

* Should we warn if purge & not aggregate

  * Do we want to add ``required_if = [('purge', 'true', ['aggregate'])]``
  * Maybe no, as we may want to factory reset a all vlans
  * Add tests for this
* Does the order matter for access controll list?
* Link to `Aggreate declaritive intent`
* Docs marker for "Reference ID"