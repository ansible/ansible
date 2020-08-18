.. _network_connection_options:

***************************************
Working with network connection options
***************************************

Network modules can support multiple connection protocols, such as ``ansible.netcommon.network_cli``, ``ansible.netcommon.netconf``, and ``ansible.netcommon.httpapi``. These connections include some common options you can set to control how the connection to your network device behaves.

Common options are:

* ``become`` and ``become_method`` as described in :ref:`privilege_escalation`.
* ``network_os`` - set to match your network platform you are communicating with. See the :ref:`platform-specific <platform_options>` pages.
* ``remote_user`` as described in :ref:`connection_set_user`.
* Timeout options - ``persistent_command_timeout``, ``persistent_connect_timeout``, and ``timeout``.

.. _timeout_options:

Setting timeout options
=======================

When communicating with a remote device, you have control over how long Ansible maintains the connection to that device, as well as how long Ansible waits for a command to complete on that device. Each of these options can be set as variables in your playbook files, environment variables, or settings in your :ref:`ansible.cfg file <ansible_configuration_settings>`.

For example, the three options for controlling the connection timeout are as follows.

Using vars (per task):

.. code-block:: yaml

  - name: save running-config
    cisco.ios.ios_command:
      commands: copy running-config startup-config
      vars:
        ansible_command_timeout: 30

Using the environment variable:

.. code-block:: bash

  $export ANSIBLE_PERSISTENT_COMMAND_TIMEOUT=30

Using the global configuration (in :file:`ansible.cfg`)

.. code-block:: ini

  [persistent_connection ]
  command_timeout = 30

See :ref:`ansible_variable_precedence` for details on the relative precedence of each of these variables. See the individual connection type to understand each option.
