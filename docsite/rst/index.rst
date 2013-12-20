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

The Basics
``````````

Before we dive into the really fun parts -- playbooks, configuration management, deployment, and orchestration, we'll learn how to get Ansible installed and some basic concepts.  We'll go over how to execute ad-hoc commands in parallel across your nodes using /usr/bin/ansible.  We'll also see what sort of modules are available in Ansible's core (though you can also write your own, which we'll also show later).

.. toctree::
   :maxdepth: 1

   intro_installation
   intro_getting_started
   intro_inventory
   intro_dynamic_inventory
   intro_patterns
   intro_adhoc
   intro_configuration

Modules
```````

Ansible modules are resources that are distributed to remote nodes to make them perform particular tasks or match a particular
state.  Ansible follows a "batteries included" philosophy, so you have a lot of great modules for all manner of
IT tasks in the core distribution.  This means modules are well up-to-date and you don't have to hunt for an implementation
that will work on your platform.  You may think of the module library as a toolbox full of useful system management tools, 
and playbooks as the instructions for building something using those tools.

.. toctree::
   :maxdepth: 1

   modules

.. _overview:

Architecture Diagram
````````````````````

.. image:: http://www.ansibleworks.com/wp-content/uploads/2013/06/ANSIBLE_DIAGRAM.jpg
   :alt: ansible architecture diagram
   :width: 788px
   :height: 436px

.. _introduction_to_playbooks:

Playbooks
`````````

Playbooks are Ansible's configuration, deployment, and orchestration language.  They can describe a policy you want your remote systems to enforce, or a set of steps in a general IT process.

If Ansible modules are the tools in your workshop, playbooks are your design plans.

At a basic level, playbooks can be used to manage configurations of and deployments to remote machines.  At a more advanced level, they can sequence multi-tier rollouts involving rolling updates, and can delegate actions to other hosts, interacting with monitoring servers and load balancers along the way.  

While there's a lot of information here, there's no need to learn everything at once.  You can start small and pick up more features
over time as you need them.  

Playbooks are designed to be human-readable and are developed in a basic text language.  There are multiple
ways to organize playbooks and the files they include, and we'll offer up some suggestions on that and making the most out of Ansible.

It is recommended to look at `Example Playbooks <https://github.com/ansible/ansible-examples>`_ while reading along with the playbook documentation.  These illustrate best practices as well as how to put many of the various concepts together.

.. toctree::
   :maxdepth: 1

   playbooks
   playbooks_roles
   playbooks_variables
   playbooks_conditionals
   playbooks_loops
   playbooks_best_practices

.. _advanced_topics_in_playbooks:

Special Topics In Playbooks
```````````````````````````

Here are some playbook features that not everyone may need to learn, but can be quite useful for particular applications. 
Browsing these topics is recommended as you may find some useful tips here, but feel free to learn the basics of Ansible first 
and adopt these only if they seem relevant or useful to your environment.

.. toctree::
   :maxdepth: 1

   playbooks_acceleration
   playbooks_async
   playbooks_checkmode
   playbooks_delegation
   playbooks_environment
   playbooks_error_handling
   playbooks_lookups
   playbooks_prompts
   playbooks_tags

.. _ansibleworks_awx:

AnsibleWorks AWX
````````````````

`AnsibleWorks <http://ansibleworks.com>`_, who also sponsors the Ansible community, also produces 'AWX', which is a web-based solution that makes Ansible even more easy to use for IT teams of all kinds.  It's designed to be the hub for all of your automation tasks.

AWX allows you to control access to who can access what, even allowing sharing of SSH credentials without someone being able to transfer those credentials.  Inventory can be graphically managed or synced with a wide variety of cloud sources.  It logs all of your jobs, integrates well with LDAP, and has an amazing browsable REST API.  Command line tools are available for easy integration
with Jenkins as well.  

Find out more about AWX features and how to download it on the `AWX webpage <http://ansibleworks.com/ansibleworks-awx>`_.  AWX
is free for usage for up to 10 nodes, and comes bundled with amazing support from AnsibleWorks.  As you would expect, AWX is
installed using Ansible playbooks!

.. _detailed_guides:    

Detailed Guides
```````````````

This section is new and evolving.  The idea here is explore particular use cases in greater depth and provide a more "top down" explanation of some basic features.

.. toctree::
   :maxdepth: 1

   guide_aws
   guide_vagrant

Pending topics may include: Docker, Jenkins, Rackspace Cloud, Google Compute Engine, Linode/Digital Ocean, Continous Deployment, and more.

.. _community_information:

Community Information
`````````````````````

Ansible is an open source project designed to bring together developers and administrators of all kinds to collaborate on building
IT automation solutions that work well for them.   Should you wish to get more involved -- whether in terms of just asking a question, helping other users, introducing new people to Ansible, or helping with the software or documentation, we welcome your contributions to the project.

`Ways to interact <https://github.com/ansible/ansible/blob/devel/CONTRIBUTING.md>`_

.. _developer_information:

Developer Information
`````````````````````

Learn how to build modules of your own in any language, and also how to extend Ansible through several kinds of plugins. Explore Ansible's Python API and write Python plugins to integrate with other solutions in your environment.

.. toctree::
   :maxdepth: 1

   developing_api
   developing_inventory
   developing_modules
   developing_plugins

Developers will also likely be interested in the fully-discoverable `REST API <http://ansibleworks.com/ansibleworks-awx>`_ that is part of AnsibleWorks AWX.  It's great for embedding Ansible in all manner of applications.

.. _misc:

Miscellaneous
`````````````

Some additional topics you may be interested in:

.. toctree::
   :maxdepth: 1

   faq
   glossary
   YAMLSyntax


