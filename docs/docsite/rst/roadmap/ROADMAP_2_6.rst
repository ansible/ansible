===========
Ansible 2.6
===========

**Core Engine Freeze:** Mid May 2018

**Core and Curated Module Freeze:** Mid May 2018

**Community Module Freeze:** Late May 2018

**Release Candidate:** Mid June 2018

**Target:** June/July 2018

.. contents:: Topics

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
* Stretch & tech preview: New connection plugin for gRPC
* Stretch: netconf plugin for IOS
* Stretch: netconf plugin for NXOS

Modules
=======

* New ``cli_config`` - platform agnostic module for sending text based config over network_cli
* New ``cli_command`` - platform agnostic command module
* New ``netconf_get`` - implements the standard netconf get rpc
* New ``netconf_rpc`` - calls any playbook defined rpc on the remote device and returns the results

Other Features
================

* Stretch & tech preview: Configuration caching for network_cli. Opt-in feature to avoid ``show running`` performance hit


Windows
-------




