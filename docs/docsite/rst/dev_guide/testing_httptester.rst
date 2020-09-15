:orphan:

**********
httptester
**********

.. contents:: Topics

Overview
========

``httptester`` is a docker container used to host certain resources required by :ref:`testing_integration`. This is to avoid CI tests requiring external resources (such as git or package repos) which, if temporarily unavailable, would cause tests to fail.

HTTP Testing endpoint which provides the following capabilities:

* httpbin
* nginx
* SSL
* SNI


Source files can be found in the `http-test-container <https://github.com/ansible/http-test-container>`_ repository.

Extending httptester
====================

If you have sometime to improve ``httptester`` please add a comment on the `Testing Working Group Agenda <https://github.com/ansible/community/blob/master/meetings/README.md>`_ to avoid duplicated effort.
