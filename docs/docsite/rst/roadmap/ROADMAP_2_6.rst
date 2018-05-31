===========
Ansible 2.6
===========

.. contents:: Topics

Release Schedule
----------------

Actual
======

- 2018-05-17 Core Freeze (Engine and Core Modules/Plugins)
- 2018-05-21 Alpha Release 1
- 2018-05-25 Community Freeze (Non-Core Modules/Plugins)
- 2018-05-25 Branch stable-2.6
- 2018-05-30 Alpha Release 2

Expected
========

- 2018-05-31 Release Candidate 1
- 2018-06-07 Release Candidate 2
- 2018-06-14 Release Candidate 3
- 2018-06-28 Final Release

Engine improvements
-------------------

- Version 2.6 is largely going to be a stabilization release for Core code.
- Some of the items covered in this release, but are not limited to are the following:

  - ``ansible-inventory``
  - ``import_*``
  - ``include_*``
  - Test coverage
  - Performance Testing

Core Modules
------------
- Adopt-a-module Campaign

  - Review current status of all Core Modules
  - Reduce backlog of open issues against these modules

Cloud Modules
-------------

Network
-------

Connection work
================

* New connection plugin: eAPI `proposal#102 <https://github.com/ansible/proposals/issues/102>`_
* New connection plugin: NX-API
* Support for configurable options for network_cli & netconf

Modules
=======

* New ``net_get`` - platform agnostic module for pulling configuration via SCP/SFTP over network_cli
* New ``net_put`` - platform agnostic module for pushing configuration via SCP/SFTP over network_cli
* New ``netconf_get`` - Netconf module to fetch configuration and state data `proposal#104 <https://github.com/ansible/proposals/issues/104>`_

Other Features
================

* Stretch & tech preview: Configuration caching for network_cli. Opt-in feature to avoid ``show running`` performance hit


Windows
-------




