.. Where to put this is a bit hard.  This document will be used while cutting releases.  As such, if
   there are problems with the document that needs to be fixed, we want to be able to do it in the
   middle of a release.  The problem arises that making changes in the middle of a release could
   cause problems like the website or tarball failing to build.  So we want to put this someplace
   where those are not problems.

   Additionally, process docs like this should go in without the docs team pre-review.  For process
   docs, sharing of the process with other committers needs to take precedence otherwise the
   committers will end up sharing the information outside of the documentation.  We desperately need
   to document our step-by-step procedures so we need to remove barriers to entry for getting those
   in.

   In addition to this doc there's a few "templates" that I've linked to hat should come into the
   repo too (template for release announcement email, etc)

Release Manager Process
=======================

This document describes the step-by-step procedures for creating a release.


Cherry-picking
--------------

* Create and populate a ``2.X.Y Blockers`` Github Project for each release (major or minor release).
  Use it to track the blocker bugs for release.

    * Use the `2.4.1 Blocker project <https://github.com/ansible/ansible/projects/11>`_ as a template.

* Leave a comment in the PR that you cherry-pick from as to what release the change will show up in
  example:

   * ``Merged to devel and cherry-picked for the 2.4.0rc3 release.``
   * Use cherry-pick -x to automatically add the SHA to the cherrypick::

        git cherry-pick -x SHA

* When cherry-picking to minor releases, add a changelog entry for every cherrypick.  Include a link
  to the PR or bug.
* For Beta periods, allow committers to use their judgement
* For RC periods, ask mattclay/a github admin to lock down permissions on the branch so that only
  the RM can cherry-pick


Pre beta1
---------

* Coordinate with Project Manager about syncing open PRs from the Roadmap blocker.  Roadmap blocker
  will have mainly features and higher level cards.

   * Decide which open ones are to be punted vs finished.
   * If to be finished one has a single PR, copy over.
   * If to be finished one has multiple PRs, ask feature owner what the PRs are and move them all
     over to the bug

* Get the permissions you will need:

   * Able to ssh and sudo on ``74.207.229.77`` (master mirror)
   * Ops in ``#ansible``
   * Access to http://jenkins.testing.ansible.com/
   * Able to post to ``ansible-announce``, ``ansible-project``, and ``ansible-devel`` mailing lists


.. _first_release:

To make beta1 for the major release
-----------------------------------

1. Create stable-2.X and push
2. Change version in stable-2.X:

    a. Change devel to 2.X in :file:`docs/docsite/_themes/srtd/layout.html`

3. Bump the **devel** version to 2.(X+1)

    a. :file:`VERSION`
    b. :file:`lib/ansible/release.py`
    c. :file:`packaging/release/vars/versions.yml`

        i. Determine a codename for 2.(X+1) (Led Zeppelin song name)

4. Run ``ansible-playbook packaging/release/release.yml``

    a. Enter the release branch: stable-2.X
    b. Enter the release version: 2.X.0.0
    c. Enter the release string (ie. 0.1.beta1, or just 1 for final releases): 0.1.beta1
    d. Does this branch have git submodules? [no]: no
    e. Is this a final release (not a beta/rc)? [no]: no
    f. Push repositories upstream when done? [no]: no

5. The release has been built into: :file:`packaging/release/ansible_release`  (as long as you use
   the local connection on localhost) cd into that directory to do the rest of the work
6. ``git log -p`` to sanity check

    a. Check :file:`VERSION`
    b. :file:`lib/ansible/release.py`

7. ``git push``
8. Wait for shippable to run on the stable-2.X branch and check that it is good

    a. https://app.shippable.com/github/ansible/ansible/dashboard

9. ``git push --tags``
10. Push sha and tarfiles out (pre-release candidates do this manually, final releases do this in
    jenkins)::

        export AUSERNAME=tkuratomi
        scp -P 5150 packaging/release/ansible_release/dist/* $AUSERNAME@74.207.229.77:
        ssh -p 5150 $AUSERNAME@74.207.229.77
        chmod 0644 ansible-*.tar.gz*
        sudo mv ~/ansible-*.tar.gz* /var/www/html/releases/ansible/
        sudo chown root:root /var/www/html/releases/ansible/ansible-*.tar.gz*

11. http://jenkins.testing.ansible.com/job/Sync_release_mirrors/

    a. Build now

12. Start the public RPM package build:

    a. http://jenkins.testing.ansible.com/job/Build_Ansible_Public_RPM_Branch/build?delay=0sec
    b. For the branch use the release tag created above.
    c. For the publish option use ``preview`` for an RC and ``release`` for a release.

13. See if the package builds worked:

    a. http://jenkins.testing.ansible.com/job/Build_Ansible_Public_RPM_Branch/

14. Send email:

    a. To ``ansible-devel``
    b. `Template <https://gist.github.com/abadger/3171f11b769150ae931498facd85c80d>`_
    c. Change the versions and the sha256sum.  Be sure to use https when copying links!
    d. Get the email link from the `googlegroup archive
       <https://groups.google.com/forum/#!forum/ansible-project>`_

15. Non-release managers, please spread the rc announcement to:

    a. Working Groups

       i. In meetings
       ii. On Agenda ticket

    b. Network - Network team responsibility, just remind them
       i. Network to code

.. note:: Step 14 and 15 should be merged with the communication section somehow


Pre rc1
-------

* Have mattclay/github org admin Tighten permissions on the ``stable-2.X`` branch so only the
  release manager can merge there
* Create the ``temp-staging-post-2.X.0`` branch for changes that are destined for the next minor
  release to be merged to::

    git checkout stable-2.4
    git checkout -b temp-staging-post-2.4.0
    git push --set-upstream origin temp-staging-post-2.4.0


.. _rc1:

To make rc1 for the major release
---------------------------------

* Steps 4-14 of the :ref:`beta1 release <first_release>`
* Email to ``ansible-project@googlegroups.com`` as well as ``ansible-devel``
* tweet the link to the release announcement
   * Send retweet request to ``@kaete`` or ``@carriedrummond`` on slack
* Change topic in ``#ansible`` irc channel similar to this:
   * ``Ansible - !search $topic - http://docs.ansible.com * latest releases: 2.3.2.0 / 2.2.3.0 / 2.1.6.0  * 2.4.0.0 RC1 - https://groups.google.com/forum/#!topic/ansible-project/uan6RTZ166Y``


Once rc1 is released
--------------------

.. note:: Check whether some of these should be done earlier: after stable-2.X has been branched, after
    beta1 has been released, etc.

.. note:: ``@shanemcd`` is our contact for jenkins issues

* Ping ``@jlaska`` or ``@gmainwaring`` to create an ansible2.(X-1) PPA so old releases can get
  pushed there
* Post a message in ``#ship_it`` in slack that the stable-2.X branch needs to be added to the tower
  test matrix
* Add version 2.X to docsite:

    * Make PR to https://github.com/ansible/docsite/blob/master/index.html, add a 2.X option to the
      dropdown
    * Hack build config at http://jenkins.testing.ansible.com/job/Build_Ansible_Docs/configure to
      pull from stable-2.X and rsync output to docs.ansible.com/2.X/ (TODO: who owns this, and should
      there be a generic stable-x.y docs build task?)
    * Re-enable automerge in devel.  For instance: https://github.com/ansible/ansible/pull/29086

* Reminder to the committers:  when merging PRs to devel, make sure that module PRs have the correct
  version added. All the ones which have already passed CI did so when it was still 2.X.

    * The ansibot command ``rebuild_merge`` is helpful for this

* Porting Guide

   * Create stub :file:`docs/docsite/rst/porting_guide_2.(X+1).rst`

      * `Template <https://github.com/ansible/ansible/commit/ac6205b9e84c26a687fb8e466a8c063f37632058>`_
      * Remember to update all 2.X -> old, 2.(X+1) -> new

   * Update :file:`docs/docsite/rst/porting_guides.rst` to point at the new file

* Ensure :file:`CHANGELOG.md` contains anchor link


Subsequent rcs of a major release
---------------------------------

* All the steps of the :ref:`rc1` release.


Leading up to the final major release
-------------------------------------

* Start Google Doc draft for release email

    * This can be done in parallel to allow Core Team time to add comments
    * Include link to porting guide
    * Link CHANGELOG to the branched version
    * Add in major features from the changelog to the release announcement
    * Ping ``@dharmabumstead`` the release announcement link

* Update the changelog

    * People should have been updating the changelog as they added major features.  Ping them to
      make sure they've done that
    * Cut and paste from the previous stable-X.Y changelog into devel so that devel has a record of
      what was in the X.Y minor releases.


To make a final major release
-----------------------------

* In the ``devel`` branch edit :file:`packaging/release/vars/versions.yml` -- Update the release
  date
* In both ``devel`` and ``stable-2.4`` branch edit release status in
  :file:`docs/docsite/rst/release_and_maintenance.rst`
* Steps 4-6 of the :ref:`beta1 <first_release>` section
* Additional final release Sanity checks

   * :file:`RELEASES.txt`
   * :file:`packaging/rpm/ansible.spec`
   * :file:`packaging/debian/changelog`

* Steps 7-9 of the :ref:`beta1 <first_release>` section
* Build and upload the tarballs/rpm/deb packages via jenkins:

   * http://jenkins.testing.ansible.com/view/Ansible/job/Release_Ansible/
   * GIT_BRANCH=origin/tags/v2.4.0.0-1
   * CONFIRM=<check it>
   * DEB_PPA=<leave as-is>
   * NOTE: the jenkins job does not generate sha256sum files

* Steps 12-13 of the :ref:`beta1 <first release>` section
* Other things to check:

   * New release on https://pypi.python.org/pypi/ansible
   * New release on https://releases.ansible.com/ansible
   * New release on the PPA https://launchpad.net/~ansible/+archive/ubuntu/ansible
   * Old release on the PPA https://launchpad.net/~ansible/+archive/ubuntu/ansible-2.3
   * New release in the rpms directory: http://releases.ansible.com/ansible/rpm/release/

* Send email to ``ansible-announce`` and ``ansible-project`` googlegroup

   * This should have been worked on with the rest of the team prior to the final rc.
   * Get the email link from the `googlegroup archive
     <https://groups.google.com/forum/#!forum/ansible-announce>`_

* Steps 16 of the :ref:`beta1 <first_release>` section

   * NOTE: We do not tweet the final releases.  Marketing handles that entirely

* Send a message to #ship_it on slack to alert tower team that the final release is out
* Email ansible-tower@redhat.com to alert tower team of final release
* Run the Jenkins DEB job to upload the latest 2.3 version to this PPA too

   * http://jenkins.testing.ansible.com/job/Build_Ansible_DEB/
   * GIT_BRANCH=v2.3.2.0-1
   * OFFICIAL=yes
   * DEB_DIST=<leave as is>
   * DEB_PPA=ppa:ansible/ansible-2.3

* Merge the ``temp-staging-post-2.4.0`` branch back into the ``stable-2.4`` branch and then remove
  the branch from the repo

   * Relax permissions on the stable-2.4 branch so that anyone can commit again


To make a dot release
---------------------

* Step 4-16 of the :ref:`beta1 <first_release>` process


Building docs
-------------

.. Should this be moved to its own page?  And then link to it at the points where docs should be
   rebuilt.  At what point should the docsite be updated? Do we need to wait for that to complete
   before sending the final email out? We may wish to kill other Commit triggered docs builds that
   are higher in the queue.

* http://jenkins.testing.ansible.com/job/Build_Ansible_Docs/build?delay=0sec (Google SSO)

   * OFFICIAL=yes
   * CLEAN: default (unchecked)
   * branch="origin/devel" or "origin/stable-2.4"
   * OLD_VERSION

      * If yes, we inhibit creating the "latest" symlink. This is intended for use when doing an official update of prior versions of the documentation.        
      * http://docs.ansible.com/ansible/latest/ should point to the latest stable release. OLD_VERSION
      * yes: For Beta/RCs and anything apart from the latest stable release
      * no: First time we want to update the latest symlink. This should only be done for vX.Y.0.0-1 build[b]

* Click Build
* If there are other GitHub documentations jobs being run, see left had "Build History", indicated by the GitHub you can click on the job then select the tiny red x from the top right which is between the progress bar and "keep this build for ever"


Communication
-------------
.. DRAFT: Who needs telling, when and how
   Combine the Freeze columns?  It looks like they're all the same.  Maybe a
   separate table of all the events that can happen

=========================  =====  ===  =====  ==================  =====================  ================  ======
Who                        Final  RCs  Betas  Core Engine Freeze  Core & Curated Freeze  Community Freeze  Branch
-------------------------  -----  ---  -----  ------------------  ---------------------  ----------------  ------
IRC #ansible-*                 x    x      x                   x                      x                 x       x
WG Agendas                     x    x                          x                      x                 x       x
Network to code                x                                                                                 
ML ansible-announce            x                                                                                 
ML Ansible-project             x    x                                                                            
ML Ansible-devel               x    x      x                   x                      x                 x       x
Twitter                        x    x                                                                            
Slack #general                                                                                                   
Slack #shipit                  x                                                                                 
Slack #core_internal           x    x      x                   x                      x                 x       x
Slack #core_networking              x      x                   x                      x                 x       x
RH Slack #ansible                                                                                                
RH Slack #ansible-network                                                                                        
=========================  =====  ===  =====  ==================  =====================  ================  ======
