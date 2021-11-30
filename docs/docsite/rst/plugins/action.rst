.. _action_plugins:

Action plugins
==============

.. contents::
   :local:
   :depth: 2

Action plugins act in conjunction with :ref:`modules <working_with_modules>` to execute the actions required by playbook tasks. They usually execute automatically in the background doing prerequisite work before modules execute.

The 'normal' action plugin is used for modules that do not already have an action plugin. If necessary, you can :ref:`create custom action plugins <developing_actions>`.

.. _enabling_action:

Enabling action plugins
-----------------------

You can enable a custom action plugin by either dropping it into the ``action_plugins`` directory adjacent to your play, inside a role, or by putting it in one of the action plugin directory sources configured in :ref:`ansible.cfg <ansible_configuration_settings>`.

.. _using_action:

Using action plugins
--------------------

Action plugin are executed by default when an associated module is used; no action is required.

Plugin list
-----------

You cannot list action plugins directly, they show up as their counterpart modules:

Use ``ansible-doc -l`` to see the list of available modules.
Use ``ansible-doc <name>`` to see specific documentation and examples, this should note if the module has a corresponding action plugin.

.. seealso::

   :ref:`cache_plugins`
       Cache plugins
   :ref:`callback_plugins`
       Callback plugins
   :ref:`connection_plugins`
       Connection plugins
   :ref:`inventory_plugins`
       Inventory plugins
   :ref:`shell_plugins`
       Shell plugins
   :ref:`strategy_plugins`
       Strategy plugins
   :ref:`vars_plugins`
       Vars plugins
   `User Mailing List <https://groups.google.com/group/ansible-devel>`_
       Have a question?  Stop by the google group!
   :ref:`communication_irc`
       How to join Ansible chat channels
