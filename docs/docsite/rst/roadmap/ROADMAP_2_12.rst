.. _core_roadmap_2_12:

=================
Ansible-core 2.12
=================

.. contents::
   :local:

Release Schedule
----------------

Expected
========

PRs must be raised well in advance of the dates below to have a chance of being included in this ansible-core release.

.. note:: There is no Alpha phase in 2.12.
.. note:: Dates subject to change.

- 2021-08-30 Feature Freeze
  No new functionality (including modules/plugins) to any code

- 2021-09-13 Beta 1
- 2021-09-20 Beta 2 (if necessary)

- 2021-10-04 Release Candidate 1 (and ``stable-2.12`` branching from ``devel``)
- 2021-10-11 Release Candidate 2 (if necessary)

- 2021-10-25 Release

Release Manager
---------------

 Ansible Core Team

Planned work
============

- Bump the minimum Python version requirement for the controller to Python 3.8. This will be a hard requirement.
- Deprecate Python 2.6 support for managed/target hosts. The release of ``ansible-core==2.13`` will remove Python 2.6 support.
- Introduce split-controller testing in ``ansible-test`` to separate dependencies for the controller from dependencies on the target.
- Extend the functionality of ``module_defaults`` ``action_groups`` to be created and presented by collections.
- Implement object proxies, to expose restricted interfaces between parts of the code, and enable deprecations of attributes and variables.
