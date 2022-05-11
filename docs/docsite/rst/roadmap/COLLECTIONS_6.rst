.. _ansible_6_roadmap:

===================
Ansible project 6.0
===================

This release schedule includes dates for the `ansible <https://pypi.org/project/ansible/>`_ package, with a few dates for the `ansible-core <https://pypi.org/project/ansible-core/>`_ package as well. All dates are subject to change. See the `ansible-core 2.13 Roadmap <https://docs.ansible.com/ansible-core/devel/roadmap/ROADMAP_2_13.html>`_ for the most recent updates on ``ansible-core``.

.. contents::
   :local:


Release schedule
=================


:2022-03-28: ansible-core feature freeze, stable-2.13 branch created.
:2022-04-11: Start of ansible-core 2.13 betas (biweekly, as needed).
:2022-04-12: Ansible-6.0.0 alpha1 (roughly biweekly ``ansible`` alphas timed to coincide with ``ansible-core-2.13`` pre-releases).
:2022-04-27: Community Meeting topic: List any backwards incompatible collection releases that beta1 should try to accommodate.
:2022-05-02: First ansible-core release candidate.
:2022-05-03: Ansible-6.0.0 alpha2.
:2022-05-11: Community Meeting topic: Decide what contingencies to activate for any blockers that do not meet the deadline.
:2022-05-16: Ansible-core-2.13 released.
:2022-05-17: Ansible-6.0.0 alpha3.
:2022-05-23: Last day for collections to make backwards incompatible releases that will be accepted into Ansible-6. This includes adding new collections to Ansible 6.0.0; from now on new collections have to wait for 6.1.0 or later.
:2022-05-24: Create the ansible-build-data directory and files for Ansible-7.
:2022-05-24: Ansible-6.0.0 beta1 -- feature freeze [1]_ (weekly beta releases; collection owners and interested users should test for bugs).
:2022-05-31: Ansible-6.0.0 beta2.
:2022-06-07: Ansible-6.0.0 rc1 [2]_ [3]_ (weekly release candidates as needed; test and alert us to any blocker bugs).  Blocker bugs will slip release.
:2022-06-21: Ansible-6.0.0 release.
:2022-07-12: Release of Ansible-6.1.0 (bugfix + compatible features: every three weeks.)

.. [1] No new modules or major features accepted after this date. In practice, this means we will freeze the semver collection versions to compatible release versions. For example, if the version of community.crypto on this date was community.crypto 2.3.0; Ansible-6.0.0 could ship with community.crypto 2.3.1.  It would not ship with community.crypto 2.4.0.

.. [2] After this date only changes blocking a release are accepted.  Accepted changes require creating a new rc and may slip the final release date.

.. [3] Collections will only be updated to a new version if a blocker is approved.  Collection owners should discuss any blockers at a community IRC meeting (before this freeze) to decide whether to bump the version of the collection for a fix. See the `Community IRC meeting agenda <https://github.com/ansible/community/issues/539>`_.

.. note::

  Breaking changes will be introduced in Ansible 6.0.0, although we encourage the use of deprecation periods that will show up in at least one Ansible release before the breaking change happens, this is not guaranteed.


Ansible minor releases
=======================

Ansible 6.x minor releases will occur approximately every three weeks if changes to collections have been made or if it is deemed necessary to force an upgrade to a later ansible-core-2.13.x.  Ansible 6.x minor releases may contain new features but not backwards incompatibilities.  In practice, this means we will include new collection versions where either the patch or the minor version number has changed but not when the major number has changed. For example, if Ansible-6.0.0 ships with community.crypto 2.3.0; Ansible-6.1.0 may ship with community.crypto 2.4.0 but would not ship with community.crypto 3.0.0.


.. note::

    Minor releases will stop when Ansible-7 is released.  See the :ref:`Release and Maintenance Page <release_and_maintenance>` for more information.


For more information, reach out on a mailing list or a chat channel - see :ref:`communication` for more details.

Planned work
============

More details can be found in `the community-topics planning issue <https://github.com/ansible-community/community-topics/issues/56>`_.

* Remove compatibility code which prevents parallel install of Ansible 6 with Ansible 2.9 or ansible-base 2.10
* Stop installing files (such as tests and development artifacts like editor configs) we have no use for
* Ship Python wheels (as ansible-core 2.13 will likely also do) to improve installation performance
