.. _modules_plugins_index:

#################################
Using Ansible modules and plugins
#################################

.. note::

    **Making Open Source More Inclusive**

    Red Hat is committed to replacing problematic language in our code, documentation, and web properties. We are beginning with these four terms: master, slave, blacklist, and whitelist. We ask that you open an issue or pull request if you come upon a term that we have missed. For more details, see `our CTO Chris Wright's message <https://www.redhat.com/en/blog/making-open-source-more-inclusive-eradicating-problematic-language>`_.

Welcome to the Ansible guide for working with modules, plugins, and collections.

Ansible modules are units of code that can control system resources or execute system commands.
Ansible provides a module library that you can execute directly on remote hosts or through playbooks.
You can also write custom modules.

Similar to modules are plugins, which are pieces of code that extend core Ansible functionality.
Ansible uses a plugin architecture to enable a rich, flexible, and expandable feature set.
Ansible ships with several plugins and lets you easily use your own plugins.

.. toctree::
   :maxdepth: 2

   modules_intro
   modules_support
   plugin_filtering_config
   ../plugins/plugins
   modules_plugins_index