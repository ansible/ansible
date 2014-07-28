Ansible Documentation
=====================

About Ansible
`````````````

Welcome to the Ansible documentation!

Ansible is an IT automation tool.  It can configure systems, deploy software, and orchestrate more advanced IT tasks
such as continuous deployments or zero downtime rolling updates.  

Ansible's goals are foremost those of simplicity and maximum ease of use. It also has a strong focus on security and reliability, featuring a minimum of moving parts, usage of OpenSSH for transport (with an accelerated socket mode and pull modes as alternatives), and a language that is designed around auditability by humans -- even those not familiar with the program.

We believe simplicity is relevant to all sizes of environments and design for busy users of all types -- whether this means developers, sysadmins, release engineers, IT managers, and everywhere in between. Ansible is appropriate for managing small setups with a handful of instances as well as enterprise environments with many thousands.

Ansible manages machines in an agentless manner. There is never a question of how to
upgrade remote daemons or the problem of not being able to manage systems because daemons are uninstalled.  As OpenSSH is one of the most peer reviewed open source components, the security exposure of using the tool is greatly reduced.  Ansible is decentralized -- it relies on your existing OS credentials to control access to remote machines; if needed it can easily connect with Kerberos, LDAP, and other centralized authentication management systems.

This documentation covers the current released version of Ansible (1.5.3) and also some development version features (1.6).  For recent features, in each section, the version of Ansible where the feature is added is indicated.  Ansible, Inc releases a new major release of Ansible approximately every 2 months.  The core application evolves somewhat conservatively, valuing simplicity in language design and setup, while the community around new modules and plugins being developed and contributed moves very very quickly, typically adding 20 or so new modules in each release.

.. _an_introduction:

.. toctree::
   :maxdepth: 1

   intro
   quickstart
   playbooks
   playbooks_special_topics
   modules
   modules_by_category
   guides
   developing
   tower
   community
   galaxy
   test_strategies
   faq
   glossary
   YAMLSyntax
   guru

