.. _release_managers:

**************************
Release Manager Guidelines
**************************

.. contents:: Topics

The release manager's purpose is to ensure a smooth release.  To achieve that goal, they need to
coordinate between:

* Developers with commit privileges on the `Ansible GitHub repository <https://github.com/ansible/ansible/>`_
* Contributors without commit privileges
* The community
* Ansible documentation team

Pre-releases: what and why
==========================

Pre-releases exist to draw testers. They give people who don't feel comfortable running from source
control a means to get an early version of the code to test and give us feedback. To ensure we get
good feedback about a release, we need to make sure all major changes in a release are put into
a pre-release. Testers must be given time to test those changes before the final release. Ideally we
want there to be sufficient time between pre-releases for people to install and test one version for
a span of time. Then they can spend more time using the new code than installing the latest
version.

The right length of time for a tester is probably around two weeks. However, for our three-to-four month
development cycle to work, we compress this down to one week; any less runs the risk
of people spending more time installing the code instead of running it. However, if there's a time
crunch (with a release date that cannot slip), it is better to release with new changes than to hold
back those changes to give people time to test between. People cannot test what is not released, so
we have to get those tarballs out there even if people feel they have to install more frequently.


Beta releases
-------------

In a beta release, we know there are still bugs.  We will continue to accept fixes for these.
Although we review these fixes, sometimes they can be invasive or potentially destabilize other
areas of the code.

During the beta, we will no longer accept feature submissions.


Release candidates
------------------

In a release candidate, we've fixed all known blockers. Any remaining bugfixes are
ones that we are willing to leave out of the release. At this point we need user testing to
determine if there are any other blocker bugs lurking.

Blocker bugs generally are those that cause significant problems for users. Regressions are
more likely to be considered blockers because they will break present users' usage of Ansible.

The Release Manager will cherry-pick fixes for new release blockers. The release manager will also
choose whether to accept bugfixes for isolated areas of the code or defer those to the next minor
release. By themselves, non-blocker bugs will not trigger a new release; they will only make it
into the next major release if blocker bugs require that a new release be made.

The last RC should be as close to the final as possible. The following things may be changed:

    * Version numbers are changed automatically and will differ as the pre-release tags are removed from
      the versions.
    * Tests and :file:`docs/docsite/` can differ if really needed as they do not break runtime.
      However, the release manager may still reject them as they have the potential to cause
      breakage that will be visible during the release process.

.. note:: We want to specifically emphasize that code (in :file:`bin/`, :file:`lib/ansible/`, and
    :file:`setup.py`) must be the same unless there are extraordinary extenuating circumstances.  If
    there are extenuating circumstances, the Release Manager is responsible for notifying groups
    which would want to test the code.


Ansible release process
=======================

The release process is kept in a `separate document
<https://docs.google.com/document/d/10EWLkMesi9s_CK_GmbZlE_ZLhuQr6TBrdMLKo5dnMAI/edit#heading=h.ooo3izcel3cz>`_
so that it can be easily updated during a release.  If you need access to edit this, please ask one
of the current release managers to add you.
