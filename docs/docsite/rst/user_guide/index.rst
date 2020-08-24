##########
User Guide
##########

Welcome to the Ansible User Guide! This guide covers how to work with Ansible, including using the command line, working with inventory, and writing playbooks. This page outlines the most common situations and questions that bring readers to this section. If you prefer a traditional table of contents, you can find one at the bottom of the page.

Getting started
===============

* I'm new to Ansible. Do you have a :ref:`quick video overview <quickstart>` of how Ansible works?
* I'm ready to learn about Ansible. What :ref:`basic_concepts` do I need to learn?
* I want to use Ansible without writing a playbook. How do I use :ref:`ad-hoc commands <intro_adhoc>`?

Using inventory
===============

* I have a list of servers and devices I want to automate. How do I create :ref:`inventory <intro_inventory>` to track them?
* I use cloud services and constantly have servers and devices starting and stopping. How do I track them using :ref:`dynamic inventory <intro_dynamic_inventory>`?
* I want to automate specific sub-sets of my inventory. How do I use :ref:`patterns <intro_patterns>`?

Interacting with data
=====================

* I want to use a single playbook against multiple systems with different attributes. How do I use :ref:`variables <playbooks_variables>` to handle the differences?
* I want to retrieve data about my systems. How do I access :ref:`Ansible facts <playbooks_vars_facts>`?
* I need to access sensitive data like passwords with Ansible. How can I protect that data with :ref:`Ansible vault <vault>`?
* I want to change the data I have, so I can use it in a task. How do I use :ref:`filters <playbooks_filters>` to transform my data?
* I need to retrieve data from an external source. How do I use :ref:`lookups <playbooks_lookups>` to access databases and APIs?
* I want to ask the person who runs my playbook to supply data. How do I get user input with :ref:`prompts <playbooks_prompts>`?

Writing tasks, plays, and playbooks
===================================

* I'm writing my first playbook. What should I :ref:`know before I begin <playbooks_tips_and_tricks>`?
* I have a specific use case for a task or play:

  * Executing tasks with elevated privileges or as a different user with :ref:`become <become>`
  * Repeating a task once for each item in a list with :ref:`loops <playbooks_loops>`
  * Executing tasks on a different machine with :ref:`delegation <playbooks_delegation>`
  * Executing tasks only when certain conditions apply with :ref:`conditionals <playbooks_conditionals>` and evaluating conditions with :ref:`tests <playbooks_tests>`
  * Grouping a set of tasks together with :ref:`blocks <playbooks_blocks>`
  * Managing task errors and failures seamlessly
  * Setting remote environment values

* I want to leverage the power of re-usable Ansible artifacts. How do I create re-usable :ref:`files <playbooks_reuse>` and :ref:`roles <playbooks_reuse_roles>`?
* I need to incorporate one file or playbook inside another. What is the difference between :ref:`including and importing <playbooks_reuse_includes>`?

Executing playbooks
===================

Once your playbook is ready to run, you may want to review these advanced topics:

* Previewing the results of my playbook with :ref:`check mode and diff <check_mode_dry>`
* Running playbooks while troubleshooting with :ref:`start and step <playbooks_startnstep>`
* Correcting tasks during execution with the :ref:`Ansible debugger <playbooks_debugger>`
* Controlling how my playbook executes with :ref:`strategies and more <playbooks_strategies>`
* Running playbooks :ref:`asynchronously <playbooks_async>`

.. toctree::
   :maxdepth: 2

Getting Started
   quickstart
   basic_concepts
   intro_getting_started
   intro_inventory
   intro_dynamic_inventory
   intro_patterns
   intro_adhoc
   connection_details
   command_line_tools
   playbooks
   become
   vault
   sample_setup
   modules
   ../plugins/plugins
   intro_bsd
   windows
   collections_using
