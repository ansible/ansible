

Ansible Documentation
`````````````````````

Welcome to the Ansible documentation.  

Ansible is an IT automation tool.  It can configure systems, deploy software, and orchestrate more advanced IT orchestration
such as continuous deployments or zero downtime rolling updates.

Ansibe's goals are foremost those of simplicity and ease of use. It also has a strong focus on security and reliability, featuring
a minimum of moving parts, usage of Open SSH for transport, and a language that is designed around auditability by humans -- even those
not familiar with the program.

This documentation covers the current released version of Ansible (1.3.X) and also some development version features (1.4).  For recent features, in each section, the version of Ansible where the feature is added is indicated.  Ansible produces a new major release approximately
every 2 months.

Before we dive into playbooks, configuration management, deployment, and orchestration, we'll learn how to get Ansible installed and some
basic information.  We'll go over how to execute ad-hoc commands in parallel across your nodes using /usr/bin/ansible.  We'll also see
what sort of modules are available in Ansible's core (though you can also write your own, which we'll also show later).

An Introduction
```````````````

.. toctree::
   :maxdepth: 1

   intro_installation
   intro_getting_started
   intro_inventory
   intro_inventory_dynamic
   intro_patterns
   intro_adhoc
   modules

Overview
````````

.. image:: http://www.ansibleworks.com/wp-content/uploads/2013/06/ANSIBLE_DIAGRAM.jpg
   :alt: ansible architecture diagram
   :width: 788px
   :height: 436px

An Introduction to Playbooks
````````````````````````````

Playbooks are Ansible's configuration, deployment, and orchestration language.  They can describe a policy you want your remote systems
to enforce, or a set of steps in a general IT process.

At a basic level, playbooks can be used to manage configurations of and deployments to remote machines.  At a more advanced level, they can sequence multi-tier rollouts involving rolling updates, and can delegate actions to other hosts, interacting with monitoring servers and load balancers along the way.  

There's no need to learn everything at once.  You can start small and pick up more features
over time as you need them.  

Playbooks are designed to be human-readable and are developed in a basic text language.  There are multiple
ways to organize playbooks and the files they include, and we'll offer up some suggestions on that and making the most out of Ansible.

.. toctree::
   :maxdepth: 1

   playbooks
   playbooks_roles
   playbooks_variables
   playbooks_loops
   playbooks_best_practices
   Example Playbooks <https://github.com/ansible/ansible-examples>

Advanced Topics In Playbooks
````````````````````````````

Here are some playbook features that not everyone may need to learn, but can be quite useful for particular applications. 
Browsing these topics is recommended as you may find some useful tips here, but feel free to learn Ansible first and adopt
these only if they seem relevant or useful to your environment::

   playbooks_acceleration
   playbooks_check_mode
   playbooks_delegation
   playbooks_environment
   playbooks_error_handling
   playbooks_lookups
   playbooks_prompts
   playbooks_strategies
    
Detailed Guides
```````````````

This section is new and evolving.  The idea here is explore particular use cases in greater depth and provide a more "top down" explanation
of some basic features.  

A chance to dive into some more topics in depth:

.. toctree::
   :maxdepth: 1

   guide_aws

Pending topics may include: Vagrant, Docker, Jenkins, Rackspace Cloud, Google Compute Engine, Linode/Digital Ocean, Continous Deployment, 
and more.

Community Information
`````````````````````

Ansible is an open source project designed to bring together developers and administrators of all kinds to collaborate on building
IT automation solutions that work well for them.   Should you wish to get more involved -- whether in terms of just asking a question, helping
other users, introducing new people to Ansible, or helping with the software or documentation, we welcome your contributions to the project::

   How to interact <https://github.com/ansible/ansible/blob/devel/CONTRIBUTING.md>

Developer Information
`````````````````````

Learn how to build modules of your own in any language, and also how to extend ansible through several kinds of plugins. Explore Ansible's Python API and write Python plugins to integrate
with other solutions in your environment.

.. toctree::
   :maxdepth: 1

   developing_contributing
   developing_code_standards
   developing_api
   developing_inventory
   developing_modules
   developing_plugins
   developing_callbacks
   developing_filters
   developing_lookups
   developing_transports
   developing_modules
   REST API <http://ansibleworks.com/ansibleworks-awx>

Miscellaneous
`````````````

.. toctree::
   :maxdepth: 1

   faq
   contrib
   glossary

