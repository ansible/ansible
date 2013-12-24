Ansible Documentation
=====================

About Ansible
`````````````

Welcome to the Ansible documentation!

Ansible is an IT automation tool.  It can configure systems, deploy software, and orchestrate more advanced IT tasks
such as continuous deployments or zero downtime rolling updates.  

Ansible's goals are foremost those of simplicity and maximum ease of use. It also has a strong focus on security and reliability, featuring a minimum of moving parts, usage of Open SSH for transport (with an accelerated socket mode and pull modes as alternatives), and a language that is designed around auditability by humans -- even those not familiar with the program.

We believe simplicity is relevant to all sizes of environments and design for busy users of all types -- whether this means developers, sysadmins, release engineers, IT managers, and everywhere in between. Ansible is appropriate for managing small setups with a handful of instances as well as enterprise environments with many thousands.

Ansible manages machines in an agentless manner. There is never a question of how to
upgrade remote daemons or the problem of not being able to manage systems because daemons are uninstalled.  As OpenSSH is one of the most peer reviewed open source components, the security exposure of using the tool is greatly reduced.  Ansible is decentralized -- it relies on your existing OS credentials to control access to remote machines; if needed it can easily connect with Kerberos, LDAP, and other centralized authentication management systems.

You may be interested in reading about `some notable Ansible users <http://www.ansibleworks.com/users/>`_.

This documentation covers the current released version of Ansible (1.4.3) and also some development version features (1.5).  For recent features, in each section, the version of Ansible where the feature is added is indicated.  AnsibleWorks releases a new major release of Ansible approximately every 2 months.  The core application evolves somewhat conservatively, valuing simplicity in language design and setup, while the community around new modules and plugins being developed and contributed moves very very quickly, typically adding 20 or so new modules in each release.

.. _an_introduction:

.. toctree::
   :maxdepth: 2

   intro
   playbooks
   playbooks_special_topics
   modules
   guides
   developing
   faq
   glossary
   YAMLSyntax

AnsibleWorks AWX
````````````````

`AnsibleWorks <http://ansibleworks.com>`_, who also sponsors the Ansible community, also produces 'AWX', which is a web-based solution that makes Ansible even more easy to use for IT teams of all kinds.  It's designed to be the hub for all of your automation tasks.

AWX allows you to control access to who can access what, even allowing sharing of SSH credentials without someone being able to transfer those credentials.  Inventory can be graphically managed or synced with a wide variety of cloud sources.  It logs all of your jobs, integrates well with LDAP, and has an amazing browsable REST API.  Command line tools are available for easy integration
with Jenkins as well.  

Find out more about AWX features and how to download it on the `AWX webpage <http://ansibleworks.com/ansibleworks-awx>`_.  AWX
is free for usage for up to 10 nodes, and comes bundled with amazing support from AnsibleWorks.  As you would expect, AWX is
installed using Ansible playbooks!

.. _ansibleworks_galaxy:

AnsibleWorks Galaxy
```````````````````

.. image:: https://galaxy.ansibleworks.com/static/img/galaxy_logo_small.png
   :alt: AnsibleWorks Galaxy Logo
   :width: 619px
   :height: 109px

`AnsibleWorks Galaxy <http://galaxy.ansibleworks.com>`_, is a free site for finding, downloading, rating, and reviewing all kinds of community developed Ansible roles and can be a great way to get a jumpstart on your automation projects.

You can sign up with social auth, and the download client 'ansible-galaxy' is included in Ansible 1.4.2 and later.

Read the "About" page on the Galaxy site for more information.

.. _detailed_guides:    

Community Information
`````````````````````

Ansible is an open source project designed to bring together developers and administrators of all kinds to collaborate on building
IT automation solutions that work well for them.   Should you wish to get more involved -- whether in terms of just asking a question, helping other users, introducing new people to Ansible, or helping with the software or documentation, we welcome your contributions to the project.

`Ways to interact <https://github.com/ansible/ansible/blob/devel/CONTRIBUTING.md>`_


