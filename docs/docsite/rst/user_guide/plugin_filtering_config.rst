.. _plugin_filtering_config:

Plugin Filter Configuration
===========================

Ansible 2.5 adds the ability for a site administrator to blacklist modules that they do not want to
be available to Ansible. This is configured via a yaml configuration file (by default,
:file:`/etc/ansible/plugin_filters.yml`). Use ``plugin_filters_cfg`` configuration
in ``defaults`` section to change this configuration file path. The format of the file is:

.. code-block:: YAML

    ---
    filter_version: '1.0'
    module_blacklist:
      # Deprecated
      - docker
      # We only allow pip, not easy_install
      - easy_install

The file contains two fields:

* a version so that it will be possible to update the format while keeping backwards
  compatibility in the future. The present version should be the string, ``"1.0"``

* a list of modules to blacklist.  Any module listed here will not be found by Ansible when it
  searches for a module to invoke for a task.

.. note::

    The ``stat`` module is required for Ansible to run. So, please make sure you do not add this module in a blacklist modules list.
