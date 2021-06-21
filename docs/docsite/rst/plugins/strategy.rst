.. _strategy_plugins:

Strategy plugins
================

.. contents::
   :local:
   :depth: 2

Strategy plugins control the flow of play execution by handling task and host scheduling. For more information on using strategy plugins and other ways to control execution order, see :ref:`playbooks_strategies`.

.. _enable_strategy:

Enabling strategy plugins
-------------------------

All strategy plugins shipped with Ansible are enabled by default. You can enable a custom strategy plugin by
putting it in one of the lookup directory sources configured in :ref:`ansible.cfg <ansible_configuration_settings>`.

.. _using_strategy:

Using strategy plugins
----------------------

Only one strategy plugin can be used in a play, but you can use different ones for each play in a playbook or ansible run. By default Ansible uses the :ref:`linear <linear_strategy>` plugin. You can change this default in Ansible :ref:`configuration <ansible_configuration_settings>` using an environment variable:

.. code-block:: shell

    export ANSIBLE_STRATEGY=free

or in the `ansible.cfg` file:

.. code-block:: ini

    [defaults]
    strategy=linear

You can also specify the strategy plugin in the play via the :ref:`strategy keyword <playbook_keywords>` in a play::

  - hosts: all
    strategy: debug
    tasks:
      - copy: src=myhosts dest=/etc/hosts
        notify: restart_tomcat

      - package: name=tomcat state=present

    handlers:
      - name: restart_tomcat
        service: name=tomcat state=restarted

.. _strategy_plugin_list:

Plugin list
-----------

You can use ``ansible-doc -t strategy -l`` to see the list of available plugins.
Use ``ansible-doc -t strategy <plugin name>`` to see plugin-specific specific documentation and examples.


.. seealso::

   :ref:`about_playbooks`
       An introduction to playbooks
   :ref:`inventory_plugins`
       Inventory plugins
   :ref:`callback_plugins`
       Callback plugins
   :ref:`filter_plugins`
       Filter plugins
   :ref:`test_plugins`
       Test plugins
   :ref:`lookup_plugins`
       Lookup plugins
   `User Mailing List <https://groups.google.com/group/ansible-devel>`_
       Have a question?  Stop by the google group!
   `irc.libera.chat <https://libera.chat/>`_
       #ansible IRC chat channel
