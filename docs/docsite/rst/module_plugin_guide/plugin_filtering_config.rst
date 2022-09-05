.. _plugin_filtering_config:

Rejecting modules
=================

If you want to avoid using certain modules, you can add them to a reject list to prevent Ansible from loading them. To reject plugins, create a yaml configuration file. The default location for this file is :file:`/etc/ansible/plugin_filters.yml`. You can select a different path for the reject list using the :ref:`PLUGIN_FILTERS_CFG` setting in the ``defaults`` section of your ansible.cfg. Here is an example reject list:

.. code-block:: YAML

    ---
    filter_version: '1.0'
    module_rejectlist:
      # Deprecated
      - docker
      # We only allow pip, not easy_install
      - easy_install

The file contains two fields:

  * A file version so that you can update the format while keeping backwards compatibility in the future. The present version should be the string, ``"1.0"``

  * A list of modules to reject. Ansible will not load any module in this list when it searches for a module to invoke for a task.

.. note::

    The ``stat`` module is required for Ansible to run. Do not add this module to your reject list.
