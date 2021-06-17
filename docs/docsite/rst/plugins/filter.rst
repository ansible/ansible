.. _filter_plugins:

Filter plugins
=============

.. contents::
   :local:
   :depth: 2

Filter plugins manipulate data. With the right filter you can extract a particular value, transform data types and formats, perform mathematical calculations, split and concatenate strings, insert dates and times, and do much more.  Ansible leverages the :ref:`standard filters <jinja2:builtin-filters>` shipped with Jinja2 and adds some specialized filter plugins. You can :ref:`create custom Ansible filters as plugins <developing_filter_plugins>`.

.. _enabling_filter:

Enabling filter plugins
----------------------

You can add a custom filter plugin by dropping it into a ``filter_plugins`` directory adjacent to your play, inside a role, or by putting it in one of the filter plugin directory sources configured in :ref:`ansible.cfg <ansible_configuration_settings>`.

.. _using_filter:

Using filter plugins
-------------------

For information on using filter plugins, see :ref:`playbooks_filters`.

.. seealso::

   :ref:`about_playbooks`
       An introduction to playbooks
   :ref:`inventory_plugins`
       Inventory plugins
   :ref:`callback_plugins`
       Callback plugins
   :ref:`test_plugins`
      Test plugins
   :ref:`lookup_plugins`
       Lookup plugins
   `User Mailing List <https://groups.google.com/group/ansible-devel>`_
       Have a question?  Stop by the google group!
   `irc.freenode.net <http://irc.freenode.net>`_
       #ansible IRC chat channel
