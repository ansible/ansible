.. _working_with_playbooks:

Working with playbooks
======================

Playbooks record and execute Ansible's configuration, deployment, and orchestration functions. They can describe a policy you want your remote systems to enforce, or a set of steps in a general IT process.

If Ansible modules are the tools in your workshop, playbooks are your instruction manuals, and your inventory of hosts are your raw material.

At a basic level, playbooks can be used to manage configurations of and deployments to remote machines.  At a more advanced level, they can sequence multi-tier rollouts involving rolling updates, and can delegate actions to other hosts, interacting with monitoring servers and load balancers along the way.

Playbooks are designed to be human-readable and are developed in a basic text language.  There are multiple ways to organize playbooks and the files they include, and we'll offer up some suggestions on that and making the most out of Ansible.

You should look at `Example Playbooks <https://github.com/ansible/ansible-examples>`_ while reading along with the playbook documentation.  These illustrate best practices as well as how to put many of the various concepts together.

.. toctree::
   :maxdepth: 2

   playbooks_templating
   playbooks_special_topics
   guide_rolling_upgrade
