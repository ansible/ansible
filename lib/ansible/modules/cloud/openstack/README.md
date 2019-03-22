OpenStack Ansible Modules
=========================

These are a set of modules for interacting with OpenStack as either an admin
or an end user. If the module does not begin with os_, it's either deprecated
or soon to be. This document serves as developer coding guidelines for
modules intended to be here.

Naming
------

* All modules should start with os_
* If the module is one that a cloud consumer would expect to use, it should be
  named after the logical resource it manages. Thus, os\_server not os\_nova.
  The reasoning for this is that there are more than one resource that are
  managed by more than one service and which one manages it is a deployment
  detail. A good example of this are floating IPs, which can come from either
  Nova or Neutron, but which one they come from is immaterial to an end user.
* If the module is one that a cloud admin would expect to use, it should be
  be named with the service and the resource, such as os\_keystone\_domain.
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
  effort should be made to present one sane interface to the ansible user
  regardless of deployer insanity.
* All modules should work appropriately against all existing known public
  OpenStack clouds.
* It should be assumed that a user may have more than one cloud account that
  they wish to combine as part of a single ansible managed infrastructure.

Libraries
---------

* All modules should use openstack\_full\_argument\_spec to pick up the
  standard input such as auth and ssl support.
* All modules should extends\_documentation\_fragment: openstack to go along
  with openstack\_full\_argument\_spec.
* All complex cloud interaction or interoperability code should be housed in
  the [openstacksdk](http://git.openstack.org/cgit/openstack/openstacksdk)
  library.
* All OpenStack API interactions should happen via the openstacksdk and not via
  OpenStack Client libraries. The OpenStack Client libraries do no have end
  users as a primary audience, they are for intra-server communication.

Testing
-------

* Integration testing is currently done in OpenStack's CI system in
  https://git.openstack.org/cgit/openstack/openstacksdk/tree/openstack/tests/ansible
* Testing in openstacksdk produces an obvious chicken-and-egg scenario. Work is under
  way to trigger from and report on PRs directly.
