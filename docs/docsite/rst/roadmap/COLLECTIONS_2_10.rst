====================
Ansible project 2.10
====================

This release schedule includes dates for the `ansible <https://pypi.org/project/ansible/>`_ package, with a few dates for the `ansible-base <https://pypi.org/project/ansible-base/>`_ package as well. All dates are subject to change. See :ref:`base_roadmap_2_10` for the most recent updates on ansible-base.

.. contents::
   :local:

Release Schedule
----------------

.. note:: Dates subject to change.
.. note:: We plan to post weekly alpha releases to the `PyPI ansible project <https://pypi.org/project/ansible/>`_ for testing.

.. warning::
    We initially were going to have feature freeze on 2020-08-18. We tried this but decided to
    change course.  Instead, we'll enter feature freeze when ansible-2.10.0 beta1 is released.

- 2020-06-23: ansible-2.10 alpha freeze.
  No net new collections will be added to the ``ansible-2.10`` package after this date.
- 2020-07-10: Ansible collections freeze date for content shuffling.
  Content should be in its final collection for the ansible-2.10 series of releases. No more content should move out of the ``community.general`` or ``community.network`` collections.
- 2020-08-13: ansible-base 2.10 Release date, see :ref:`base_roadmap_2_10`.
- 2020-08-14: final ansible-2.10 alpha.
- 2020-09-01: ansible-2.10.0 beta1 and feature freeze.

  - No new modules or major features will be added after this date. In practice this means we will freeze the semver collection versions to compatible release versions. For example, if the version of community.crypto on this date was community-crypto-1.1.0; ansible-2.10.0 could ship with community-crypto-1.1.1.  It would not ship with community-crypto-1.2.0.

- 2020-09-08: ansible-2.10.0 beta2.
- 2020-09-15: ansible-2.10.0 rc1 and final freeze.

  - After this date only changes blocking a release are accepted.
  - Collections will only be updated to a new version if a blocker is approved.  Collection owners should discuss any blockers at the community IRC meeting (on 9-17) to decide whether to bump the version of the collection for a fix. See the `Community IRC meeting agenda <https://github.com/ansible/community/issues/539>`_.

** Additional release candidates to be published as needed as blockers are fixed **

- 2020-09-22: ansible-2.10 GA release date.

Ansible-2.10.x patch releases will occur roughly every three weeks if changes to collections have been made or if it is deemed necessary to force an upgrade to a later ansible-base-2.10.x.  Ansible-2.10.x patch releases may contain new features but not backwards incompatibilities.  In practice, this means we will include new collection versions where either the patch or the minor version number has changed but not when the major number has changed (example: Ansible-2.10 ships with community-crypto-1.1.0; ansible-2.10.1 may ship with community-crypto-1.2.0 but would not ship with community-crypto-2.0.0).


.. note::

    Minor releases will stop when :ref:`Ansible-3 <ansible_3_roadmap>` is released.  See the :ref:`Release and Maintenance Page <release_and_maintenance>` for more information.


Breaking changes may be introduced in ansible-3.0 although we encourage collection owners to use deprecation periods that will show up in at least one Ansible release before being changed incompatibly.


For more information, reach out on a mailing list or an IRC channel - see :ref:`communication` for more details.
