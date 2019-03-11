.. _working_with_playbooks:

Working With Playbooks
======================

Playbooks are Ansible's configuration, deployment, and orchestration language. They can describe a policy you want your remote systems to enforce, or a set of steps in a general IT process.

If Ansible modules are the tools in your workshop, playbooks are your instruction manuals, and your inventory of hosts are your raw material.

At a basic level, playbooks can be used to manage configurations of and deployments to remote machines.  At a more advanced level, they can sequence multi-tier rollouts involving rolling updates, and can delegate actions to other hosts, interacting with monitoring servers and load balancers along the way.

While there's a lot of information here, there's no need to learn everything at once.  You can start small and pick up more features
over time as you need them.

Playbooks are designed to be human-readable and are developed in a basic text language.  There are multiple
ways to organize playbooks and the files they include, and we'll offer up some suggestions on that and making the most out of Ansible.

You should look at `Example Playbooks <https://github.com/ansible/ansible-examples>`_ while reading along with the playbook documentation.  These illustrate best practices as well as how to put many of the various concepts together.

.. toctree::
   :maxdepth: 2

   playbooks_intro
   playbooks_reuse
   playbooks_variables
   playbooks_templating
   playbooks_conditionals
   playbooks_loops
   playbooks_blocks
   playbooks_special_topics
   playbooks_strategies
   playbooks_best_practices
   guide_rolling_upgrade
