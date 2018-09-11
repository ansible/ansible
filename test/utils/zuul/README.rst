Zuul configuration
==================

.. contents:: Topics

This directory contains the configuration for testing Ansible Network via Software Factory's Zuul instance.


Dashboard
=========

* `Zuul Status <https://ansible.softwarefactory-project.io/zuul/status.html>`_
* `List of Zuul jobs <https://ansible.softwarefactory-project.io/zuul/jobs.html>`_
* `Historical list of Zuul Jobs <https://ansible.softwarefactory-project.io/zuul/builds.html>`_

Configuration
=============

The configuration is split across the following locations

Webhook
^^^^^^^

FIXME

Software Factory tenant configuration
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

In Software Factory's ``config`` project we define `tenant-ansible <https://softwarefactory-project.io/cgit/config/tree/resources/tenant-ansible.yaml>`_



ansible/zuul-config
^^^^^^^^^^^^^^^^^^^

* `List of GitHub repos that Zuul will use <https://github.com/ansible/zuul-config/blob/master/resources/ansible.yaml>`_
* The active GitHub repos can be see on the `Zuul Projects <https://ansible.softwarefactory-project.io/zuul/projects.html>`_ page.
* Minimal, non-branched configuration. Shouldn't change often.


ansible/ansible
^^^^^^^^^^^^^^^

To allow what and how we test to be updated over time, while still allowing tests to run against older we are storing as much of the Zuul configuration in the Ansible repo as possible.

* ``.zuul.d/jobs.yaml`` - Lists the ``jobs`` that should be run
* ``test/utils/zuul/playbooks/``- Maps hosts (``nodeset``) to roles
* ``test/utils/zuul/playbooks/*/roles`` - The actual tests

