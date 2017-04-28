*******************************************
Testing using the Legacy Integration system
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


Running Cloud Tests
====================

Cloud tests exercise capabilities of cloud modules (e.g. ec2_key).  These are
not 'tests run in the cloud' so much as tests that leverage the cloud modules
and are organized by cloud provider.

Some AWS tests may use environment variables. It is recommended to either unset any AWS environment variables( such as ``AWS_DEFAULT_PROFILE``, ``AWS_SECRET_ACCESS_KEY``, etc) or be sure that the environment variables match the credentials provided in ``credentials.yml`` to ensure the tests run with consistency to their full capability on the expected account. See `AWS CLI docs <http://docs.aws.amazon.com/cli/latest/userguide/cli-chap-getting-started.html>`_ for information on creating a profile.

Subsets of tests may be run by ``#commenting`` out unnecessary roles in the appropriate playbook, such as ``test/integration/amazon.yml``.

In order to run cloud tests, you must provide access credentials in a file
named ``credentials.yml``. A sample credentials file named
``credentials.template`` is available for syntax help.


Provide cloud credentials::

    cp credentials.template credentials.yml
    ${EDITOR:-vi} credentials.yml


Other configuration
===================

In order to run some tests, you must provide access credentials in a file
named ``credentials.yml``. A sample credentials file named
``credentials.template`` is available for syntax help.

Running Tests
=============

The tests are invoked via a ``Makefile``.

If you haven't already got Ansible available use the local checkout by doing::

  source hacking/env-setup

Run the tests by doing::

  cd test/integration/
  # TARGET is the name of the test from the list at the top of this page
  #make TARGET
  # e.g.
  make amazon
  # To run all cloud tests you can do:
  make cloud

.. warning:: Possible cost of running cloud tests

   Running cloud integration tests will create and destroy cloud
   resources. Running these tests may result in additional fees associated with
   your cloud account. Care is taken to ensure that created resources are
   removed. However, it is advisable to inspect your AWS console to ensure no
   unexpected resources are running.

