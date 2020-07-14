.. _plugin_filtering_config:

Blacklisting modules
====================

If you want to avoid using certain modules, you can blacklist them to prevent Ansible from loading them. To blacklist plugins, create a yaml configuration file. The default location for this file is :file:`/etc/ansible/plugin_filters.yml`, or you can select a different path for the blacklist file using the :ref:`PLUGIN_FILTERS_CFG` setting in the ``defaults`` section of your ansible.cfg. Here is an example blacklist file:

.. code-block:: YAML

    ---
    filter_version: '1.0'
    module_blacklist:
      # Deprecated
      - docker
      # We only allow pip, not easy_install
      - easy_install

The file contains two fields:

  * A file version so that you can update the format while keeping backwards compatibility in the future. The present version should be the string, ``"1.0"``

  * A list of modules to blacklist. Any module in this list will not be loaded by Ansible when it searches for a module to invoke for a task.

.. note::

    You cannot blacklist the ``stat`` module, as it is required for Ansible to run.
