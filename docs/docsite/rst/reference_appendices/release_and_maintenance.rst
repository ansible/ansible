.. _release_and_maintenance:

Release and maintenance
=======================

.. contents::
   :local:

.. _release_cycle:

Release cycle
`````````````

Ansible is developed and released on a flexible 4 months release cycle.
This cycle can be extended in order to allow for larger changes to be properly
implemented and tested before a new release is made available.

Ansible has a graduated support structure that extends to three major releases.
For more information, read about the :ref:`development_and_stable_version_maintenance_workflow` or
see the chart in :ref:`release_schedule` for the degrees to which current releases are supported.

If you are using a release of Ansible that is no longer supported, we strongly
encourage you to upgrade as soon as possible in order to benefit from the
latest features and security fixes.

Older, unsupported versions of Ansible can contain unfixed security
vulnerabilities (*CVE*).

You can refer to the :ref:`porting guides<porting_guides>` for tips on updating your Ansible
playbooks to run on newer versions.

.. _release_schedule:

Release status
``````````````
This table links to the release notes for each major release. These release notes (changelogs) contain the dates and significant changes in each minor release.

==============================      =================================================
Ansible Release                     Status
==============================      =================================================
devel                               In development (2.9 unreleased, trunk)
`2.8 Release Notes`_                Supported (security **and** general bug fixes)
`2.7 Release Notes`_                Supported (security **and** critical bug fixes)
`2.6 Release Notes`_                Supported (security fixes)
`2.5 Release Notes`_                Unsupported (end of life)
`2.4 Release Notes`_                Unsupported (end of life)
`2.3 Release Notes`_                Unsupported (end of life)
`2.2 Release Notes`_                Unsupported (end of life)
`2.1 Release Notes`_                Unsupported (end of life)
`2.0 Release Notes`_                Unsupported (end of life)
`1.9 Release Notes`_                Unsupported (end of life)
<1.9                                Unsupported (end of life)
==============================      =================================================

You can download the releases from `<https://releases.ansible.com/ansible/>`_.

.. note:: Ansible support lasts for 3 releases.  Thus the latest Ansible release receives
    security and general bug fixes when it is first released, security and critical bug fixes when
    the next Ansible version is released, and **only** security fixes once the follow on to that version is released.

.. Comment: devel used to point here but we're currently revamping our changelog process and have no
   link to a static changelog for devel _2.6: https://github.com/ansible/ansible/blob/devel/CHANGELOG.md
.. _2.8 Release Notes:
.. _2.8: https://github.com/ansible/ansible/blob/stable-2.8/changelogs/CHANGELOG-v2.8.rst
.. _2.7 Release Notes: https://github.com/ansible/ansible/blob/stable-2.7/changelogs/CHANGELOG-v2.7.rst
.. _2.6 Release Notes:
.. _2.6: https://github.com/ansible/ansible/blob/stable-2.6/changelogs/CHANGELOG-v2.6.rst
.. _2.5 Release Notes: https://github.com/ansible/ansible/blob/stable-2.5/changelogs/CHANGELOG-v2.5.rst
.. _2.4 Release Notes:
.. _2.4: https://github.com/ansible/ansible/blob/stable-2.4/CHANGELOG.md
.. _2.3 Release Notes: https://github.com/ansible/ansible/blob/stable-2.3/CHANGELOG.md
.. _2.2 Release Notes: https://github.com/ansible/ansible/blob/stable-2.2/CHANGELOG.md
.. _2.1 Release Notes: https://github.com/ansible/ansible/blob/stable-2.1/CHANGELOG.md
.. _2.0 Release Notes: https://github.com/ansible/ansible/blob/stable-2.0/CHANGELOG.md
.. _1.9 Release Notes: https://github.com/ansible/ansible/blob/stable-1.9/CHANGELOG.md

.. _support_life:
.. _methods:

.. _development_and_stable_version_maintenance_workflow:

Development and stable version maintenance workflow
```````````````````````````````````````````````````

The Ansible community develops and maintains Ansible on GitHub_.

New modules, plugins, features and bugfixes will always be integrated in what will become the next
major version of Ansible.  This work is tracked on the ``devel`` git branch.

Ansible provides bugfixes and security improvements for the most recent major release. The previous
major release will only receive fixes for security issues and critical bugs. Ansible only applies
security fixes to releases which are two releases old. This work is tracked on the
``stable-<version>`` git branches.

The fixes that land in supported stable branches will eventually be released
as a new version when necessary.

Note that while there are no guarantees for providing fixes for unsupported
releases of Ansible, there can sometimes be exceptions for critical issues.

.. _GitHub: https://github.com/ansible/ansible

.. _release_changelogs:

Changelogs
~~~~~~~~~~

Older versions logged changes in ``stable-<version>`` branches at ``stable-<version>/CHANGELOG.md``. For example, here is the changelog for 2.4_ on GitHub.

We now generate changelogs based on fragments. Here is the generated changelog for 2.8_ as an example. When creating new features or fixing bugs, create a changelog fragment describing the change. A changelog entry is not needed for new modules or plugins. Details for those items will be generated from the module documentation.

We've got :ref:`examples and instructions on creating changelog fragments <changelogs_how_to>` in the Community Guide.


Release candidates
~~~~~~~~~~~~~~~~~~

Before a new release or version of Ansible can be done, it will typically go
through a release candidate process.

This provides the Ansible community the opportunity to test Ansible and report
bugs or issues they might come across.

Ansible tags the first release candidate (``RC1``) which is usually scheduled
to last five business days. The final release is done if no major bugs or
issues are identified during this period.

If there are major problems with the first candidate, a second candidate will
be tagged (``RC2``) once the necessary fixes have landed.
This second candidate lasts for a shorter duration than the first.
If no problems have been reported after two business days, the final release is
done.

More release candidates can be tagged as required, so long as there are
bugs that the Ansible core maintainers consider should be fixed before the
final release.

.. _release_freezing:

Feature freeze
~~~~~~~~~~~~~~

While there is a pending release candidate, the focus of core developers and
maintainers will on fixes towards the release candidate.

Merging new features or fixes that are not related to the release candidate may
be delayed in order to allow the new release to be shipped as soon as possible.


Deprecation Cycle
`````````````````

Sometimes we need to remove a feature, normally in favor of a reimplementation that we hope does a better job.
To do this we have a deprecation cycle. First we mark a feature as 'deprecated'. This is normally accompanied with warnings
to the user as to why we deprecated it, what alternatives they should switch to and when (which version) we are scheduled
to remove the feature permanently.

The cycle is normally across 4 feature releases (2.x.y, where the x marks a feature release and the y a bugfix release),
so the feature is normally removed in the 4th release after we announce the deprecation.
For example, something deprecated in 2.5 will be removed in 2.9, assuming we don't jump to 3.x before that point.
The tracking is tied to the number of releases, not the release numbering.

For modules/plugins, we keep the documentation after the removal for users of older versions.

.. seealso::

   :ref:`community_committer_guidelines`
       Guidelines for Ansible core contributors and maintainers
   :ref:`testing_strategies`
       Testing strategies
   :ref:`ansible_community_guide`
       Community information and contributing
   `Ansible release tarballs <https://releases.ansible.com/ansible/>`_
       Ansible release tarballs
   `Development Mailing List <https://groups.google.com/group/ansible-devel>`_
       Mailing list for development topics
   `irc.freenode.net <http://irc.freenode.net>`_
       #ansible IRC chat channel
