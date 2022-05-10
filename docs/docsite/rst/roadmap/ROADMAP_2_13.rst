.. _core_roadmap_2_13:

*****************
Ansible-core 2.13
*****************

.. contents::
   :local:

Release Schedule
================

Expected
--------

PRs must be raised well in advance of the dates below to have a chance of being included in this ansible-core release.

.. note:: There is no Alpha phase in 2.13.
.. note:: Dates subject to change.

Development Phase
^^^^^^^^^^^^^^^^^

The ``milestone`` branch will be advanced at the start date of each development phase.

- 2021-09-27 Development Phase 1
- 2021-12-13 Development Phase 2
- 2022-02-14 Development Phase 3

Release Phase
^^^^^^^^^^^^^

- 2022-03-28 Feature Freeze (and ``stable-2.13`` branching from ``devel``)
  No new functionality (including modules/plugins) to any code

- 2022-04-11 Beta 1
- 2022-04-25 Beta 2 (if necessary)

- 2022-05-02 Release Candidate 1

- 2022-05-16 Release

Release Manager
===============

 Ansible Core Team

Planned work
============

* ``ansible-doc`` extended dump support for devtools integration
* ``ansible-galaxy`` CLI collection verification, source, and trust
* ``jinja2`` 3.0+ dependency
* Consolidate template handling to always use ``jinja2`` native
* Drop Python 2.6 support for module execution
* Update the collection loader to Python 3.x loader API, due to removal of the Python 2 API in Python 3.12
* Modernize python packaging and installation

Delayed work
============

The following work has been delayed and retargeted for a future release

* Data Tagging
* Implement sidecar docs to support documenting filter/test plugins, as well as non Python modules
