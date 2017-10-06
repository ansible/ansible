Release Managers
================

The release manager's (RM's) duty is to coordinate between developers, docs, and Tower to ensure
a smooth release.


Pre-releases: What and Why
--------------------------

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


What is Beta?
~~~~~~~~~~~~~

In a Beta release, we know there are still bugs.  We will continue to accept fixes for these.
Although we review these fixes, sometimes they can be invasive or potentially destabilize other
areas of the code.

During the beta, we will no longer accept feature submissions.


What is a Release Candidate?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

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
    :file:`setup.py`) must be the same unless there are extraordinary extenuating circumstances.


Release Process
===============

The release process is kept in a `separate document
<https://github.com/ansible/ansible/blob/devel/release-procedure.rst>`_ so that it can be easily
updated during a release.
