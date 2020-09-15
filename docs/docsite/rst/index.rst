.. _ansible_documentation:

Ansible Documentation
=====================

About Ansible
`````````````

Ansible is an IT automation tool.  It can configure systems, deploy software, and orchestrate more advanced IT tasks such as continuous deployments or zero downtime rolling updates.

Ansible's main goals are simplicity and ease-of-use. It also has a strong focus on security and reliability, featuring a minimum of moving parts, usage of OpenSSH for transport (with other transports and pull modes as alternatives), and a language that is designed around auditability by humans--even those not familiar with the program.

We believe simplicity is relevant to all sizes of environments, so we design for busy users of all types: developers, sysadmins, release engineers, IT managers, and everyone in between. Ansible is appropriate for managing all environments, from small setups with a handful of instances to enterprise environments with many thousands of instances.

You can learn more at `AnsibleFest <https://www.ansible.com/ansiblefest>`_, the annual event for all Ansible contributors, users, and customers hosted by Red Hat. AnsibleFest is the place to connect with others, learn new skills, and find a new friend to automate with.

Ansible manages machines in an agent-less manner. There is never a question of how to upgrade remote daemons or the problem of not being able to manage systems because daemons are uninstalled.  Because OpenSSH is one of the most peer-reviewed open source components, security exposure is greatly reduced. Ansible is decentralized--it relies on your existing OS credentials to control access to remote machines. If needed, Ansible can easily connect with Kerberos, LDAP, and other centralized authentication management systems.

This documentation covers the version of Ansible noted in the upper left corner of this page. We maintain multiple versions of Ansible and of the documentation, so please be sure you are using the version of the documentation that covers the version of Ansible you're using. For recent features, we note the version of Ansible where the feature was added.

Ansible releases a new major release of Ansible approximately three to four times per year. The core application evolves somewhat conservatively, valuing simplicity in language design and setup. Contributors develop and change modules and plugins, hosted in collections since version 2.10, much more quickly.

.. toctree::
   :maxdepth: 2
   :caption: Installation, Upgrade & Configuration

   installation_guide/index
   porting_guides/porting_guides

.. toctree::
   :maxdepth: 2
   :caption: Using Ansible

   user_guide/index

.. toctree::
   :maxdepth: 2
   :caption: Contributing to Ansible

   community/index

.. toctree::
   :maxdepth: 2
   :caption: Extending Ansible

   dev_guide/index

.. toctree::
   :glob:
   :maxdepth: 1
   :caption: Common Ansible Scenarios

   scenario_guides/cloud_guides
   scenario_guides/network_guides
   scenario_guides/virt_guides

.. toctree::
   :maxdepth: 2
   :caption: Ansible for Network Automation

   network/index

.. toctree::
   :maxdepth: 2
   :caption: Ansible Galaxy

   galaxy/user_guide.rst
   galaxy/dev_guide.rst


.. toctree::
   :maxdepth: 1
   :caption: Reference & Appendices

   ../modules/modules_by_category
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
   reference_appendices/logging


.. toctree::
   :maxdepth: 2
   :caption: Release Notes

.. toctree::
   :maxdepth: 2
   :caption: Roadmaps

   roadmap/index.rst
