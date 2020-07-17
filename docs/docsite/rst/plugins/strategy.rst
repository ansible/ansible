.. _strategy_plugins:

Strategy Plugins
================

.. contents::
   :local:
   :depth: 2

Strategy plugins control the flow of play execution by handling task and host scheduling.

.. _enable_strategy:

Enabling strategy plugins
-------------------------

All strategy plugins shipped with Ansible are enabled by default. You can enable a custom strategy plugin by
putting it in one of the lookup directory sources configured in :ref:`ansible.cfg <ansible_configuration_settings>`.

.. _using_strategy:

Using strategy plugins
----------------------

Only one strategy plugin can be used in a play, but you can use different ones for each play in a playbook or ansible run.
The default is the :ref:`linear <linear_strategy>` plugin. You can change this default in Ansible :ref:`configuration <ansible_configuration_settings>` using an environment variable:

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
       Ansible inventory plugins
   :ref:`callback_plugins`
       Ansible callback plugins
   :ref:`playbooks_filters`
       Jinja2 filter plugins
   :ref:`playbooks_tests`
       Jinja2 test plugins
   :ref:`playbooks_lookups`
       Jinja2 lookup plugins
   `User Mailing List <https://groups.google.com/group/ansible-devel>`_
       Have a question?  Stop by the google group!
   `irc.freenode.net <http://irc.freenode.net>`_
       #ansible IRC chat channel
