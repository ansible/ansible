.. _core_branches_and_tags:

******************************************
``ansible-core`` project branches and tags
******************************************

``devel`` branch
================

All new development on the next version of ``ansible-core`` occurs exclusively in the ``devel`` branch,
and all bugfixes to prior releases must first be merged to devel before being backported to one or more stable branches
for inclusion in servicing releases. Around the Beta 1 milestone, a new ``stable-X.Y`` branch is cut from ``devel``,
which is then updated to host development of the ``X.Y+1`` release. External automated testing of Ansible content from
``devel`` is not generally recommended.

``stable-X.Y`` branches
=======================

All ``ansible-core`` ``X.Y.Z`` releases are created from a corresponding ``stable-X.Y`` branch. A
release's stable branch is typically cut from ``devel`` around ``X.Y.0 beta 1`` (when the release is feature complete).
All further bugfixes (no enhancements!) must be made against ``devel`` and backported to applicable stable branches.

``vX.Y.Z`` tags
===============

Each ``ansible-core vX.Y.Z`` release is tagged from the release commit in the corresponding ``stable-X.Y`` branch,
allowing access to the exact source used to create the release. As of ``ansible-core`` 2.13, the auto-generated GitHub
tarball of the tag contents is considered the official canonical release artifact.


.. _milestone_branch:

``milestone`` branch
====================

A ``milestone`` branch is a slow-moving stream of the ``devel`` branch, intended for external testing of ``ansible-core``
features under active development. As described in the :ref:`ansible_core_roadmaps` for a given release, development is
typically split into three phases of decreasing duration, with larger and more invasive changes targeted to be merged to
``devel`` in earlier phases. The ``milestone`` branch is updated to the contents of ``devel`` at the end of each
development phase. This allows testing of semi-stable unreleased features on a predictable schedule without the exposure
to the potential instability of the daily commit "fire hose" from ``devel``. When a release reaches the Beta 1 milestone,
the ``milestone`` branch will be updated to the first ``devel`` commit after the version number has been increased.
Further testing of the same release should be done from the new ``stable-X.Y`` branch that was created. If a severe issue
that significantly affects community testing or stability is discovered in the ``milestone`` branch, the branch contents
may require unscheduled adjustment, but not in a way that prevents fast-forward updates (for example, ``milestone``-only
commits will not be created or cherry-picked from ``devel``).

The following example is for illustrative purposes only. See the :ref:`ansible_core_roadmaps` for accurate dates. For example, the ``milestone`` branch in 2.13 ``ansible-core`` roadmap updated as follows:

* 27-Sep-2021: 2.13 Development Phase 1 begins; ``milestone`` contents are updated to 2.12.0b1 with version number set to
  ``2.13.0.dev0``. Automated content testing that includes version-specific ignore files (e.g., ``ignore-2.12.txt``)
  should copy them for the current version (e.g., ``ignore-2.13.txt``) before this point to ensure that automated sanity
  testing against the ``milestone`` branch will continue to pass.
* 13-Dec-2021: 2.13 Development Phase 2 begins; ``milestone`` contents are updated to the final commit from Development Phase 1
* 14-Feb-2022: 2.13 Development Phase 3 begins; ``milestone`` contents are updated to the final commit from Development Phase 2
* 11-Apr-2022: ``stable-2.13`` branch created with results from Development Phase 3 and freeze. ``2.13.0b1`` is released from
  ``stable-2.13``. Automated content testing should continue 2.13 series testing against the new branch. The ``devel``
  version number is updated to ``2.14.0.dev0``, and ``milestone`` is updated to that point.
