

Ansible Documentation
`````````````````````

.. image:: http://ansible.cc/docs/_static/ansible_fest_2013.png
   :alt: ansiblefest 2013
   :target: http://ansibleworks.com/fest


This page contains documentation about how to use `Ansible <http://ansible.cc>`_.  You may also be interested in taking a class:

.. image:: http://www.ansibleworks.com.s3-website-us-east-1.amazonaws.com/img/banners/training.png
   :alt: ansibleworks training
   :target: http://www.ansibleworks.com/training/

Before we dive into playbooks, configuration management, deployment, and orchestration, we'll learn how to get Ansible installed and some
basic information.  We'll go over how to execute ad-hoc commands in parallel across your nodes using /usr/bin/ansible.  We'll also see 
what sort of modules are available in Ansible's core (though you can also write your own, which we'll also show later).


.. toctree::
   :maxdepth: 1

   gettingstarted
   patterns
   examples
   modules

Overview
````````

.. image:: http://ansible.cc/img/ansible_arch.png
   :alt: ansible architecture diagram  
   :width: 566px
   :height: 439px


Playbooks
`````````

Playbooks are Ansible's orchestration language.  At a basic level, playbooks can be used to manage configurations and deployments
of remote machines.  At a more advanced level, they can sequence multi-tier rollouts involving rolling updates, and can delegate actions
to other hosts, interacting with monitoring servers and load balancers along the way.  You can start small and pick up more features 
over time as you need them.  Playbooks are designed to be human-readable and are developed in a basic text language.  There are multiple
ways to organize playbooks and the files they include, and we'll offer up some suggestions on that and making the most out of Ansible.

.. toctree::
   :maxdepth: 1

   playbooks
   playbooks2
   bestpractices
   YAMLSyntax
   Example Playbooks <https://github.com/ansible/ansible-examples>

Developer Information
`````````````````````

Learn how to build modules of your own in any language.   Explore Ansible's Python API and write Python plugins to integrate
with other solutions in your environment.

.. toctree::
   :maxdepth: 1

   api
   moduledev

Miscellaneous
`````````````

`Learn and share neat Ansible tricks on Coderwall <https://coderwall.com/p/t/ansible>`_ - sign-in using GitHub or Twitter to vote on top tips and add your own!

`A list of some Ansible users and quotes about Ansible <http://www.ansibleworks.com/users>`_.

More links:

.. toctree::
   :maxdepth: 1

   contrib
   glossary

