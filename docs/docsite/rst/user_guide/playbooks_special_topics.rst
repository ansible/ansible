.. _playbooks_special_topics:

Advanced Playbooks Features
===========================

As you write more playbooks and roles, you might have some special use cases. For example, you may want to execute "dry runs" of your playbooks (:ref:`check_mode_dry`), ask playbook users to supply information (:ref:`playbooks_prompts`), retrieve information from an external datastore or API (:ref:`lookup_plugins`), or change the way Ansible handles failures (:ref:`playbooks_error_handling`). The topics listed on this page cover these use cases and many more. If you cannot achieve your goals with basic Ansible concepts and actions, browse through these topics for help with your use case.

.. toctree::
   :maxdepth: 1

   become
   playbooks_async
   playbooks_checkmode
   playbooks_debugger
   playbooks_delegation
   playbooks_environment
   playbooks_error_handling
   playbooks_advanced_syntax
   complex_data_manipulation
   ../plugins/plugins
   playbooks_prompts
   playbooks_tags
   vault
   playbooks_startnstep
   ../reference_appendices/playbooks_keywords
   playbooks_lookups
   playbooks_module_defaults
