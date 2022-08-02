.. _core_roadmap_2.14:

*****************
Ansible-core 2.14
*****************

.. contents::
   :local:

Release Schedule
================

Expected
--------

PRs must be raised well in advance of the dates below to have a chance of being included in this ansible-core release.

.. note:: Dates subject to change.

Development Phase
^^^^^^^^^^^^^^^^^

The ``milestone`` branch will be advanced at the start date of each development phase.

- 2022-05-02 Development Phase 1
- 2022-06-27 Development Phase 2
- 2022-08-08 Development Phase 3

Release Phase
^^^^^^^^^^^^^

- 2022-09-19 Feature Freeze (and ``stable-2.14`` branching from ``devel``)
  No new functionality (including modules/plugins) to any code

- 2022-09-26 Beta 1

- 2022-10-17 Release Candidate 1

- 2022-11-07 Release

.. note:: The beta and release candidate schedules allow for up to 3 releases on a weekly schedule depending on the necessity of creating a release.

Release Manager
===============

 Ansible Core Team

Planned work
============

* Implement sidecar docs to support documenting filter/test plugins, as well as non Python modules
* Proxy Display over queue from forks
* Move handler processing into new PlayIterator phase to use the configured strategy
* Convert FieldAttribute to data descriptors to avoid complex meta classes
* Drop Python 3.8 support for controller
* Enforce running controller code with the Python locale and filesystem encoding set to UTF-8

Delayed work
============

The following work has been delayed and retargeted for a future release:

* Data Tagging
