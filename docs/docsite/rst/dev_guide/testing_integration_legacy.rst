*******************************************
Testing using the legacy Integration system
*******************************************

.. contents:: Topics

This page details how to run the integration tests that haven't been ported to the new ``ansible-test`` framework.

The following areas are still tested using the legacy ``make tests`` command:

* amazon 
* azure
* cloudflare
* cloudscale
* cloudstack
* consul
* exoscale
* gce
* jenkins
* rackspace

Over time the above list will be reduced as tests are ported to the ``ansible-test`` framework.


Running Legacy Integration Tests
=================================

FIXME Setup environment LINK

The tests are invoked via a ``Makefile``::

  # If you haven't already got Ansible available use the local checkout by doing:
  source hacking/env-setup
   
  cd test/integration/
  # TARGET is the name of the test from the list at the top of this page
  #make TARGET
  # e.g.
  make amazon