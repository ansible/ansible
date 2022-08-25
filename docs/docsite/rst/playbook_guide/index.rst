.. _playbook_guide_index:

#######################
Using Ansible playbooks
#######################

.. note::

    **Making Open Source More Inclusive**

    Red Hat is committed to replacing problematic language in our code, documentation, and web properties. We are beginning with these four terms: master, slave, blacklist, and whitelist. We ask that you open an issue or pull request if you come upon a term that we have missed. For more details, see `our CTO Chris Wright's message <https://www.redhat.com/en/blog/making-open-source-more-inclusive-eradicating-problematic-language>`_.

Welcome to the Ansible playbooks guide.
Playbooks are automation blueprints, in ``YAML`` format, that Ansible uses to deploy and configure nodes in an inventory.
This guide introduces you to playbooks and then covers different use cases for tasks and plays, such as:

* Executing tasks with elevated privileges or as a different user.
* Using loops to repeat tasks for items in a list.
* Delegating playbooks to execute tasks on different machines.
* Running conditional tasks and evaluating conditions with playbook tests.
* Using blocks to group sets of tasks.

You can also learn how to use Ansible playbooks more effectively by creating re-usable files and roles, including and importing playbooks, and running selected parts of a playbook with tags.

.. toctree::
   :maxdepth: 2

   playbooks_intro
   playbooks
   playbooks_execution
   playbooks_advanced_syntax