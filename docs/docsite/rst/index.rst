.. _ansible_documentation:

Ansible Documentation
=====================

About Ansible
`````````````

Ansible is an IT automation tool.  It can configure systems, deploy software, and orchestrate more advanced IT tasks such as continuous deployments or zero downtime rolling updates.

Ansible's main goals are simplicity and ease-of-use. It also has a strong focus on security and reliability, featuring a minimum of moving parts, usage of OpenSSH for transport (with other transports and pull modes as alternatives), and a language that is designed around auditability by humans--even those not familiar with the program.

We believe simplicity is relevant to all sizes of environments, so we design for busy users of all types: developers, sysadmins, release engineers, IT managers, and everyone in between. Ansible is appropriate for managing all environments, from small setups with a handful of instances to enterprise environments with many thousands of instances.

Ansible manages machines in an agent-less manner. There is never a question of how to
upgrade remote daemons or the problem of not being able to manage systems because daemons are uninstalled.  Because OpenSSH is one of the most peer-reviewed open source components, security exposure is greatly reduced. Ansible is decentralized--it relies on your existing OS credentials to control access to remote machines. If needed, Ansible can easily connect with Kerberos, LDAP, and other centralized authentication management systems.

This documentation covers the current released version of Ansible (2.5) and also some development version features.  For recent features, we note in each section the version of Ansible where the feature was added.

Ansible releases a new major release of Ansible approximately every two months.  The core application evolves somewhat conservatively, valuing simplicity in language design and setup. However, the community around new modules and plugins being developed and contributed moves very quickly, adding many new modules in each release.


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
   :maxdepth: 2
   :caption: Scenario Guides

   scenario_guides/guide_aci
   scenario_guides/guide_aws
   scenario_guides/guide_azure
   scenario_guides/guide_cloudstack
   scenario_guides/guide_docker
   scenario_guides/guide_gce
   scenario_guides/guide_packet
   scenario_guides/guide_rax
   scenario_guides/guide_rolling_upgrade
   scenario_guides/guide_vagrant

.. toctree::
   :maxdepth: 2
   :caption: Ansible for VMWare

   vmware/index

.. toctree::
   :maxdepth: 2
   :caption: Ansible for Network Automation

   network/index
   network/getting_started/index

.. toctree::
   :maxdepth: 2
   :caption: Reference & Appendices

   ../modules/modules_by_category
   reference_appendices/playbooks_keywords
   reference_appendices/galaxy
   reference_appendices/common_return_values
   reference_appendices/config
   reference_appendices/YAMLSyntax
   reference_appendices/python_3_support
   reference_appendices/release_and_maintenance
   reference_appendices/test_strategies
   dev_guide/testing/sanity/index
   reference_appendices/faq
   reference_appendices/glossary
   reference_appendices/tower


.. toctree::
   :maxdepth: 2
   :caption: Release Notes

.. toctree::
   :maxdepth: 2
   :caption: Roadmaps

   roadmap/index.rst
