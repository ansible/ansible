.. _OpenStack_module_development:

OpenStack Ansible Modules
=========================

These are a set of modules for interacting with OpenStack as either an admin
or an end user. If the module does not begin with ``os_``, it's either deprecated
or soon to be. This document serves as developer coding guidelines for
modules intended to be here.

.. contents::
   :local:

Naming
------

* All module names should start with ``os_``
* Name any module that a cloud consumer would expect to use after the logical resource it manages: ``os_server`` not ``os_nova``. This naming convention acknowledges that the end user does not care which service manages the resource - that is a deployment detail. For example cloud consumers may not know whether their floating IPs are managed by Nova or Neutron.
* Name any module that a cloud admin would expect to use with the service and the resource: ``os_keystone_domain``.
* If the module is one that a cloud admin and a cloud consumer could both use,
  the cloud consumer rules apply.

Interface
---------

* If the resource being managed has an id, it should be returned.
* If the resource being managed has an associated object more complex than
  an id, it should also be returned.

Interoperability
----------------

* It should be assumed that the cloud consumer does not know a bazillion
  details about the deployment choices their cloud provider made, and a best
  effort should be made to present one sane interface to the Ansible user
  regardless of deployer insanity.
* All modules should work appropriately against all existing known public
  OpenStack clouds.
* It should be assumed that a user may have more than one cloud account that
  they wish to combine as part of a single Ansible-managed infrastructure.

Libraries
---------

* All modules should use ``openstack_full_argument_spec`` to pick up the
  standard input such as auth and ssl support.
* All modules should include ``extends_documentation_fragment: openstack``.
* All complex cloud interaction or interoperability code should be housed in
  the `openstacksdk <https://git.openstack.org/cgit/openstack/openstacksdk>`_
  library.
* All OpenStack API interactions should happen via the openstacksdk and not via
  OpenStack Client libraries. The OpenStack Client libraries do no have end
  users as a primary audience, they are for intra-server communication.

Testing
-------

* Integration testing is currently done in `OpenStack's CI system <https://git.openstack.org/cgit/openstack/openstacksdk/tree/openstack/tests/ansible>`_
* Testing in openstacksdk produces an obvious chicken-and-egg scenario. Work is under
  way to trigger from and report on PRs directly.
