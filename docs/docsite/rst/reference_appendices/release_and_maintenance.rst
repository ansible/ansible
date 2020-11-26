.. _release_and_maintenance:

Release and maintenance
=======================

This section describes the Ansible and ``ansible-base`` releases. Ansible is the package that most users install. ``ansible-base`` is primarily for developers.

.. contents::
   :local:

.. _release_cycle:

Ansible release cycle
-----------------------

Ansible is developed and released on a flexible release cycle.
This cycle can be extended in order to allow for larger changes to be properly
implemented and tested before a new release is made available. See :ref:`roadmaps` for upcoming release details.

For Ansible version 2.10 or later, the major release is maintained for one release cycle. When the next release comes out (for example, 2.11), the older release (2.10 in this example) is no longer maintained.

If you are using a release of Ansible that is no longer maintained, we strongly
encourage you to upgrade as soon as possible in order to benefit from the
latest features and security fixes.

Older, unmaintained versions of Ansible can contain unfixed security
vulnerabilities (*CVE*).

You can refer to the :ref:`porting guides<porting_guides>` for tips on updating your Ansible
playbooks to run on newer versions. For Ansible 2.10 and later releases, you can install the Ansible package with ``pip``. See :ref:`intro_installation_guide` for details.  For older releases, You can download the Ansible release from `<https://releases.ansible.com/ansible/>`_.




This table links to the release notes for each major Ansible release. These release notes (changelogs) contain the dates and significant changes in each minor release.

==================================      =================================================
Ansible Release                         Status
==================================      =================================================
devel                                   In development (2.11 unreleased, trunk)
`2.10 Release Notes`_                   In development (2.10 alpha/beta)
`2.9 Release Notes`_                    Maintained (security **and** general bug fixes)
`2.8 Release Notes`_                    Maintained (security fixes)
`2.7 Release Notes`_                    Unmaintained (end of life)
`2.6 Release Notes`_                    Unmaintained (end of life)
`2.5 Release Notes`_                    Unmaintained (end of life)
<2.5                                    Unmaintained (end of life)
==================================      =================================================


.. Comment: devel used to point here but we're currently revamping our changelog process and have no
   link to a static changelog for devel _2.6: https://github.com/ansible/ansible/blob/devel/CHANGELOG.md
.. _2.10 Release Notes:
.. _2.10: https://github.com/ansible-community/ansible-build-data/blob/main/2.10/CHANGELOG-v2.10.rst
.. _2.9 Release Notes:
.. _2.9: https://github.com/ansible/ansible/blob/stable-2.9/changelogs/CHANGELOG-v2.9.rst
.. _2.8 Release Notes:
.. _2.8: https://github.com/ansible/ansible/blob/stable-2.8/changelogs/CHANGELOG-v2.8.rst
.. _2.7 Release Notes: https://github.com/ansible/ansible/blob/stable-2.7/changelogs/CHANGELOG-v2.7.rst
.. _2.6 Release Notes:
.. _2.6: https://github.com/ansible/ansible/blob/stable-2.6/changelogs/CHANGELOG-v2.6.rst
.. _2.5 Release Notes: https://github.com/ansible/ansible/blob/stable-2.5/changelogs/CHANGELOG-v2.5.rst


ansible-base release cycle
-------------------------------

``ansible-base`` is developed and released on a flexible release cycle.
This cycle can be extended in order to allow for larger changes to be properly
implemented and tested before a new release is made available. See :ref:`roadmaps` for upcoming release details.

``ansible-base`` has a graduated maintenance structure that extends to three major releases.
For more information, read about the :ref:`development_and_stable_version_maintenance_workflow` or
see the chart in :ref:`release_schedule` for the degrees to which current releases are maintained.

If you are using a release of ``ansible-base`` that is no longer maintained, we strongly
encourage you to upgrade as soon as possible in order to benefit from the
latest features and security fixes.

Older, unmaintained versions of ``ansible-base`` can contain unfixed security
vulnerabilities (*CVE*).

You can refer to the :ref:`porting guides<porting_guides>` for tips on updating your Ansible
playbooks to run on newer versions.

You can install ``ansible-base`` with ``pip``. See :ref:`intro_installation_guide` for details.

.. note:: ``ansible-base`` maintenance continues for 3 releases.  Thus the latest release receives
    security and general bug fixes when it is first released, security and critical bug fixes when
    the next ``ansible-base`` version is released, and **only** security fixes once the follow on to that version is released.


.. _release_schedule:


This table links to the release notes for each major ``ansible-base`` release. These release notes (changelogs) contain the dates and significant changes in each minor release.

==================================      =================================================
    ``ansible-base`` Release                         Status
==================================      =================================================
devel                                   In development (2.11 unreleased, trunk)
`2.10 ansible-base Release Notes`_      Maintained (security **and** general bug fixes)
==================================      =================================================


.. _2.10 ansible-base Release Notes:
.. _2.10-base: https://github.com/ansible/ansible/blob/stable-2.10/changelogs/CHANGELOG-v2.10.rst
.. _support_life:
.. _methods:

.. _development_and_stable_version_maintenance_workflow:

Development and stable version maintenance workflow
-----------------------------------------------------

The Ansible community develops and maintains Ansible and ``ansible-base`` on GitHub_.

Collection updates (new modules, plugins, features and bugfixes) will always be integrated in what will become the next version of Ansible. This work is tracked within the individual collection repositories.

Ansible and ``ansible-base`` provide bugfixes and security improvements for the most recent major release. The previous
major release of ``ansible-base`` will only receive fixes for security issues and critical bugs.``ansible-base`` only applies
security fixes to releases which are two releases old. This work is tracked on the
``stable-<version>`` git branches.

The fixes that land in maintained stable branches will eventually be released
as a new version when necessary.

Note that while there are no guarantees for providing fixes for unmaintained
releases of Ansible, there can sometimes be exceptions for critical issues.

.. _GitHub: https://github.com/ansible/ansible

.. _release_changelogs:

Changelogs
^^^^^^^^^^^^

We generate changelogs based on fragments. Here is the generated changelog for 2.9_ as an example. When creating new features or fixing bugs, create a changelog fragment describing the change. A changelog entry is not needed for new modules or plugins. Details for those items will be generated from the module documentation.

We've got :ref:`examples and instructions on creating changelog fragments <changelogs_how_to>` in the Community Guide.


Release candidates
^^^^^^^^^^^^^^^^^^^

Before a new release or version of Ansible or ``ansible-base`` can be done, it will typically go
through a release candidate process.

This provides the Ansible community the opportunity to test these releases and report
bugs or issues they might come across.

Ansible and ``ansible-base`` tag the first release candidate (``RC1``) which is usually scheduled
to last five business days. The final release is done if no major bugs or
issues are identified during this period.

If there are major problems with the first candidate, a second candidate will
be tagged (``RC2``) once the necessary fixes have landed.
This second candidate lasts for a shorter duration than the first.
If no problems have been reported after two business days, the final release is
done.

More release candidates can be tagged as required, so long as there are
bugs that the Ansible  or ``ansible-base`` core maintainers consider should be fixed before the
final release.

.. _release_freezing:

Feature freeze
^^^^^^^^^^^^^^^

While there is a pending release candidate, the focus of core developers and
maintainers will on fixes towards the release candidate.

Merging new features or fixes that are not related to the release candidate may
be delayed in order to allow the new release to be shipped as soon as possible.


Deprecation Cycle
------------------

Sometimes we need to remove a feature, normally in favor of a reimplementation that we hope does a better job.
To do this we have a deprecation cycle. First we mark a feature as 'deprecated'. This is normally accompanied with warnings
to the user as to why we deprecated it, what alternatives they should switch to and when (which version) we are scheduled
to remove the feature permanently.

Ansible deprecation cycle
^^^^^^^^^^^^^^^^^^^^^^^^^

Since Ansible is a package of individual collections, the deprecation cycle depends on the collection maintainers. We recommend the collection maintainers deprecate a feature in one Ansible major version and do not remove that feature for one year, or at least until the next major Ansible version. For example, deprecate the feature in 2.10.2, and do not remove the feature until 2.12.0.  Collections should use semantic versioning, such that the major collection version cannot be changed within an Ansible major version. Thus the removal should not happen before the next major Ansible release. This is up to each collection maintainer and cannot be guaranteed.

ansible-base deprecation cycle
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The cycle is normally across 4 feature releases (2.x.y, where the x marks a feature release and the y a bugfix release),
so the feature is normally removed in the 4th release after we announce the deprecation.
For example, something deprecated in 2.7 will be removed in 2.11, assuming we don't jump to 3.x before that point.
The tracking is tied to the number of releases, not the release numbering.

For modules/plugins, we keep the documentation after the removal for users of older versions.

.. seealso::

   :ref:`community_committer_guidelines`
       Guidelines for Ansible core contributors and maintainers
   :ref:`testing_strategies`
       Testing strategies
   :ref:`ansible_community_guide`
       Community information and contributing
   `Development Mailing List <https://groups.google.com/group/ansible-devel>`_
       Mailing list for development topics
   `irc.freenode.net <http://irc.freenode.net>`_
       #ansible IRC chat channel
