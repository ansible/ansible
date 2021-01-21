.. _ansible_core_documentation:

Ansible Core Documentation
===========================

About ansible-core
------------------

``ansible-core`` is the language, or engine,  behind Ansible, an IT automation tool.  ``ansible-core`` provides the ability to configure systems, deploy software, and orchestrate more advanced IT tasks such as continuous deployments or zero downtime rolling updates.

You can learn more at `AnsibleFest <https://www.ansible.com/ansiblefest>`_, the annual event for all Ansible contributors, users, and customers hosted by Red Hat. AnsibleFest is the place to connect with others, learn new skills, and find a new friend to automate with.

``ansible-core`` manages machines in an agent-less manner. There is never a question of how to upgrade remote daemons or the problem of not being able to manage systems because daemons are uninstalled.  Since OpenSSH is one of the most peer-reviewed open source components, security exposure is greatly reduced. Ansible is decentralized--it relies on your existing OS credentials to control access to remote machines. If needed, Ansible can easily connect with Kerberos, LDAP, and other centralized authentication management systems.

This documentation covers the version of ``ansible-core`` noted in the upper left corner of this page. We maintain multiple versions of ``ansible-core`` and of the documentation, so verify you are using the version of the documentation that covers the version of ``ansible-core`` you are using. For recent features, we note the version of Ansible where the feature was added.

``ansible-core`` releases a new major release approximately twice a year, valuing simplicity in language design and setup. Contributors develop and change modules and plugins, hosted in collections since version 2.10, much more quickly.

.. toctree::
   :maxdepth: 2
   :caption: Installation, Upgrade & Configuration

   installation_guide/index
   porting_guides/porting_guides

.. toctree::
   :maxdepth: 2
   :caption: Using ansible-core

   user_guide/index

.. toctree::
   :maxdepth: 2
   :caption: Contributing to ansible-core

   community/index

.. toctree::
   :maxdepth: 2
   :caption: Extending ansible-core

   dev_guide/index

.. toctree::
   :maxdepth: 1
   :caption: Reference & Appendices

   collections/index
   collections/all_plugins
   reference_appendices/playbooks_keywords
   reference_appendices/common_return_values
   reference_appendices/config
   reference_appendices/general_precedence
   reference_appendices/YAMLSyntax
   reference_appendices/python_3_support
   reference_appendices/interpreter_discovery
   reference_appendices/release_and_maintenance
   reference_appendices/test_strategies
   dev_guide/testing/sanity/index
   reference_appendices/faq
   reference_appendices/glossary
   reference_appendices/module_utils
   reference_appendices/special_variables
   reference_appendices/tower
   reference_appendices/automationhub
   reference_appendices/logging


.. toctree::
   :maxdepth: 2
   :caption: Release Notes

.. toctree::
   :maxdepth: 2
   :caption: Roadmaps

   roadmap/index.rst
