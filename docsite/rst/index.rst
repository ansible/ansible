Ansible Documentation
=====================

About Ansible
`````````````

Welcome to the Ansible documentation!

Ansible is an IT automation tool.  It can configure systems, deploy software, and orchestrate more advanced IT tasks
such as continuous deployments or zero downtime rolling updates.  

Ansible's main goals are simplicity and ease-of-use. It also has a strong focus on security and reliability, featuring a minimum of moving parts, usage of OpenSSH for transport (with an accelerated socket mode and pull modes as alternatives), and a language that is designed around auditability by humans--even those not familiar with the program.

We believe simplicity is relevant to all sizes of environments, so we design for busy users of all types: developers, sysadmins, release engineers, IT managers, and everyone in between. Ansible is appropriate for managing all environments, from small setups with a handful of instances to enterprise environments with many thousands of instances.

Ansible manages machines in an agent-less manner. There is never a question of how to
upgrade remote daemons or the problem of not being able to manage systems because daemons are uninstalled.  Because OpenSSH is one of the most peer-reviewed open source components, security exposure is greatly reduced. Ansible is decentralized--it relies on your existing OS credentials to control access to remote machines. If needed, Ansible can easily connect with Kerberos, LDAP, and other centralized authentication management systems.

This documentation covers the current released version of Ansible (2.0.1) and also some development version features (2.1).  For recent features, we note in each section the version of Ansible where the feature was added.  

Ansible, Inc. releases a new major release of Ansible approximately every two months.  The core application evolves somewhat conservatively, valuing simplicity in language design and setup. However, the community around new modules and plugins being developed and contributed moves very quickly, typically adding 20 or so new modules in each release.

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
   porting_guide_2.0

