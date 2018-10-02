.. _release_and_maintenance:

Release and maintenance
=======================

.. contents:: Topics
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

===============   ==========================   =================================================
Ansible Release   Latest Version               Status
===============   ==========================   =================================================
devel             2.8 (unreleased, trunk)      In development
`2.7`_            2.7.0 (2018-10-04)           Supported (security **and** general bug fixes)
`2.6`_            2.6.5 (2018-09-28)           Supported (security **and** critical bug fixes)
`2.5`_            2.5.9 (2018-09-10)           Supported (security fixes)
`2.4`_            2.4.6 (2018-07-05)           Unsupported (end of life)
`2.3`_            2.3.3 (2017-12-20)           Unsupported (end of life)
`2.2`_            2.2.3 (2017-05-09)           Unsupported (end of life)
`2.1`_            2.1.6 (2017-06-01)           Unsupported (end of life)
`2.0`_            2.0.2 (2016-04-19)           Unsupported (end of life)
`1.9`_            1.9.6 (2016-04-15)           Unsupported (end of life)
<1.9              n/a                          Unsupported (end of life)
===============   ==========================   =================================================

.. note:: Starting with Ansible-2.4, support lasts for 3 releases.  Thus Ansible-2.4 will receive
    security and general bug fixes when it is first released, security and critical bug fixes when
    2.5 is released, and **only** security fixes once 2.6 is released.

.. Comment: devel used to point here but we're currently revamping our changelog process and have no
   link to a static changelog for devel _2.6: https://github.com/ansible/ansible/blob/devel/CHANGELOG.md
.. _2.7: https://github.com/ansible/ansible/blob/stable-2.7/changelogs/CHANGELOG-v2.7.rst
.. _2.6: https://github.com/ansible/ansible/blob/stable-2.6/changelogs/CHANGELOG-v2.6.rst
.. _2.5: https://github.com/ansible/ansible/blob/stable-2.5/changelogs/CHANGELOG-v2.5.rst
.. _2.4: https://github.com/ansible/ansible/blob/stable-2.4/CHANGELOG.md
.. _2.3: https://github.com/ansible/ansible/blob/stable-2.3/CHANGELOG.md
.. _2.2: https://github.com/ansible/ansible/blob/stable-2.2/CHANGELOG.md
.. _2.1: https://github.com/ansible/ansible/blob/stable-2.1/CHANGELOG.md
.. _2.0: https://github.com/ansible/ansible/blob/stable-2.0/CHANGELOG.md
.. _1.9: https://github.com/ansible/ansible/blob/stable-1.9/CHANGELOG.md

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

.. note:: Support for three major releases began with Ansible-2.4. Ansible-2.3 and older versions
    are only supported for two releases with the first stage including both security and general bug
    fixes while the second stage includes security and critical bug fixes

The fixes that land in supported stable branches will eventually be released
as a new version when necessary.

Note that while there are no guarantees for providing fixes for unsupported
releases of Ansible, there can sometimes be exceptions for critical issues.

.. _GitHub: https://github.com/ansible/ansible

.. _changelogs_how_to:

Changelogs
~~~~~~~~~~~~~~~~~~

Older versions logged changes in ``stable-<version>`` branches at ``stable-<version>/CHANGELOG.md``. For example, here is the changelog for 2.4_ on GitHub.

We now generate changelogs based on fragments. Here is the generated changelog for 2.6_ as an example. When creating new features or fixing bugs, create a changelog fragment describing the change. A changelog entry is not needed for new modules or plugins. Details for those items will be generated from the module documentation.

Creating New Fragments
----------------------

Create a new file with a unique and descriptive name in ``changelogs/fragments/`` that ends in ``.yaml`` such as ``user-40696-backup-shadow-file.yaml``

A single changelog fragment may contain multiple sections but most will only contain one section. Here are the valid sections and a description of each:

**major_changes**
    Major changes to Ansible itself. Generally does not include module or plugin changes.

**minor_changes**
  Minor changes to Ansible, modules, or plugins. This includes new features, new parameters added to modules, or behavior changes to existing parameters.

**deprecated_features**
  Features that have been deprecated and are scheduled for removal in a future release.

**removed_features**
  Features that were previously deprecated and are now removed.

**bugfixes**
  Fixes that resolve issues. If there is a specific issue related to this bugfix, add a link in the changelog entry.

**known_issues**
  Known issues that are currently not fixed or will not be fixed.

Most changelog entries will be ``bugfixes`` or ``minor_changes``. When writing a changelog entry that pertains to a particular module, start the entry with ``- [module name] -`` and include a link to the related issue if one exists. Here are some examples:

.. code-block:: yaml

  bugfixes:
    - win_updates - fixed issue where running win_updates on async fails without any error

.. code-block:: yaml

  minor_changes:
    - lineinfile - add warning when using an empty regexp (https://github.com/ansible/ansible/issues/29443)

Commit the changelog fragment and include it with the pull request.



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
