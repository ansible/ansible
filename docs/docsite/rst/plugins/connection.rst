.. _connection_plugins:

Connection plugins
==================

.. contents::
   :local:
   :depth: 2

Connection plugins allow Ansible to connect to the target hosts so it can execute tasks on them. Ansible ships with many connection plugins, but only one can be used per host at a time.

By default, Ansible ships with several connection plugins. The most commonly used are the :ref:`paramiko SSH<paramiko_ssh_connection>`, native ssh (just called :ref:`ssh<ssh_connection>`), and :ref:`local<local_connection>` connection types.  All of these can be used in playbooks and with :command:`/usr/bin/ansible` to decide how you want to talk to remote machines. If necessary, you can :ref:`create custom connection plugins <developing_connection_plugins>`.

The basics of these connection types are covered in the :ref:`getting started<intro_getting_started>` section.

.. _ssh_plugins:

``ssh`` plugins
---------------

Because ssh is the default protocol used in system administration and the protocol most used in Ansible, ssh options are included in the command line tools. See :ref:`ansible-playbook` for more details.

.. _enabling_connection:

Adding connection plugins
-------------------------

You can extend Ansible to support other transports (such as SNMP or message bus) by dropping a custom plugin
into the ``connection_plugins`` directory.

.. _using_connection:

Using connection plugins
------------------------

You can set the connection plugin globally via :ref:`configuration<ansible_configuration_settings>`, at the command line (``-c``, ``--connection``), as a :ref:`keyword <playbook_keywords>` in your play, or by setting a :ref:`variable<behavioral_parameters>`, most often in your inventory.
For example, for Windows machines you might want to set the :ref:`winrm <winrm_connection>` plugin as an inventory variable.

Most connection plugins can operate with minimal configuration. By default they use the :ref:`inventory hostname<inventory_hostnames_lookup>` and defaults to find the target host.

Plugins are self-documenting. Each plugin should document its configuration options. The following are connection variables common to most connection plugins:

:ref:`ansible_host<magic_variables_and_hostvars>`
    The name of the host to connect to, if different from the :ref:`inventory <intro_inventory>` hostname.
:ref:`ansible_port<faq_setting_users_and_ports>`
    The ssh port number, for :ref:`ssh <ssh_connection>` and :ref:`paramiko_ssh <paramiko_ssh_connection>` it defaults to 22.
:ref:`ansible_user<faq_setting_users_and_ports>`
    The default user name to use for log in. Most plugins default to the 'current user running Ansible'.

Each plugin might also have a specific version of a variable that overrides the general version. For example, ``ansible_ssh_host`` for the :ref:`ssh <ssh_connection>` plugin.

.. _connection_plugin_list:

Plugin list
-----------

You can use ``ansible-doc -t connection -l`` to see the list of available plugins.
Use ``ansible-doc -t connection <plugin name>`` to see detailed documentation and examples.


.. seealso::

   :ref:`Working with Playbooks<working_with_playbooks>`
       An introduction to playbooks
   :ref:`callback_plugins`
       Callback plugins
   :ref:`filter_plugins`
       Filter plugins
   :ref:`test_plugins`
       Test plugins
   :ref:`lookup_plugins`
       Lookup plugins
   :ref:`vars_plugins`
       Vars plugins
   `User Mailing List <https://groups.google.com/group/ansible-devel>`_
       Have a question?  Stop by the google group!
   `irc.libera.chat <https://libera.chat/>`_
       #ansible IRC chat channel
