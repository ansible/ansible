.. _ansible_community_guide:

***********************
Ansible Community Guide
***********************

.. note::

    **Making Open Source More Inclusive**

    Red Hat is committed to replacing problematic language in our code, documentation, and web properties. We are beginning with these four terms: master, slave, blacklist, and whitelist. We ask that you open an issue or pull request if you come upon a term that we have missed. For more details, see `our CTO Chris Wright's message <https://www.redhat.com/en/blog/making-open-source-more-inclusive-eradicating-problematic-language>`_.

Welcome to the Ansible Community Guide!

The purpose of this guide is to teach you everything you need to know about being a contributing member of the Ansible community. All types of contributions are welcome and necessary to Ansible's continued success.


.. _community_toc:

.. toctree::
   :maxdepth: 2

   getting_started
   contributions

* How do I :ref:`contribute to an Ansible-maintained collection <contributing_maintained_collections>`?


Working with the Ansible repo
=============================

* I want to make my first code changes to a collection or to ``ansible-core``. How do I :ref:`set up my Python development environment <environment_setup>`?
* I would like to get more efficient as a developer. How can I find :ref:`editors, linters, and other tools <other_tools_and_programs>` that will support my Ansible development efforts?
* I want my code to meet Ansible's guidelines. Where can I find  guidance on :ref:`coding in Ansible <developer_guide>`?
* I would like to connect Ansible to a new API or other resource. How do I :ref:`create a collection <developing_modules_in_groups>`?
* My pull request is marked ``needs_rebase``. How do I :ref:`rebase my PR <rebase_guide>`?
* I am using an older version of Ansible and want a bug fixed in my version that has already been fixed on the ``devel`` branch. How do I :ref:`backport a bugfix PR <backport_process>`?
* I have an open pull request with a failing test. How do I learn about Ansible's :ref:`testing (CI) process <developing_testing>`?
* I am ready to step up as a collection maintainer. What are the :ref:`guidelines for maintainers <maintainers>`?
* A module in a collection I maintain is obsolete. How do I :ref:`deprecate a module <deprecating_modules>`?

.. _community_toc:

Traditional Table of Contents
=============================

If you prefer to read the entire Community Guide, here is a list of the pages in order:

.. toctree::
   :maxdepth: 2

   code_of_conduct
   how_can_I_help
   reporting_bugs_and_features
   documentation_contributions
   communication
   development_process
   contributing_maintained_collections
   contributor_license_agreement
   triage_process
   other_tools_and_programs
   ../dev_guide/style_guide/index

.. toctree::
   :caption: Guidelines for specific types of contributors
   :maxdepth: 1

   committer_guidelines
   maintainers
   release_managers
   github_admins
