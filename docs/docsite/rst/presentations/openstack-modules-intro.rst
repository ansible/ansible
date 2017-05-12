==================================
Intro to Ansible OpenStack Modules
==================================

This document contains a presentation in `presentty`_ format. If you want to
walk through it like a presentation, install `presentty` and run:

.. code:: bash

    presentty docs/docsite/rst/presentations/openstack-modules-intro.rst

The content is hopefully helpful even if it's not being narrated, so it's being
included in the `shade` docs.

.. _presentty: https://pypi.python.org/pypi/presentty

Ansible: Community, Collaboration, and the OpenStack Modules you know and love
==============================================================================

This talk is Free Software
==========================

* Written for presentty (https://pypi.python.org/pypi/presentty)
* docs/docsite/rst/presentations/openstack-modules-intro.rst

Ansible OpenStack Modules
=========================

* http://docs.ansible.com/ansible/list_of_cloud_modules.html#openstack
* focused on consuming OpenStack APIs
* Some are end-user focused
* Some are deployer focused

Work on All OpenStack Clouds
============================

Don't let the existence of Rackspace modules fool you. The OpenStack
modules work just great on Rackspace.

Work Around Deployer Differences ... To a Point
===============================================

* Herculean effort is made to hide a giant amount of differences
* Even so - some bugs are EWONTFIX

A provider decided to redefine the OpenStack AZ concept complete
with API changes. That is unsupportable.

Based on Shade
==============

* abstracts deployment differences
* designed for multi-cloud
* simple to use
* massive scale

  * optional advanced features to handle 20k servers a day

* Initial logic/design extracted from nodepool
* Librified to re-use in Ansible

Integration Testing
===================

* Every shade patch is integration tested in OpenStack Infra
* Every shade patch tests the ansible modules in Infra too
* Support coming soon to test PRs to modules in Infra

Let's Take a Few Steps Back
===========================

OpenStack in Ansible and Multi-cloud Operations are easy...

but you need to know a few things.

* Module structure
* Terminology
* Config

Module Structure
================

* All modules start with `os_`
* End-user oriented modules are named for the resource

  * os_image
  * os_sever

* Operator oriented modules are named for the service

  * os_nova_flavor
  * os_keystone_domain

* If it could go both ways, we prefer user orientation

  * os_user
  * os_group

* If more than one service provides a resource, they DTRT

  * os_security_group
  * os_floating_ip

OpenStack Dynamic Inventory Script
==================================

* github.com/ansible/ansible/contrib/inventory/openstack.py
* Uses all hosts in all clouds as one inventory
* Excludes hosts without IPs
* Makes a bunch of auto-groups (flavor, image, az, region, cloud)
* Makes groups for `metadata['groups']`

Modules for All OpenStack Resources are Welcome Upstream
========================================================

* If there is a thing you want to manage without a module, add one
* We're very welcoming/accepting
* Same goes for features to existing modules

To Serve All Users, We Do Have to be Strict
===========================================

* Modules that touch OpenStack APIs must do so via `shade`
* Other modules don't need to (ex: `os_tempest_config`)
* In user modules, vendor differences should be hidden
* In operator modules, exposing them is ok

clouds.yaml
===========

Information about the clouds you want to connect to is stored in a file
called `clouds.yaml`.

Both `yaml` and `yml` are acceptable.

`clouds.yaml` can be in your homedir: `~/.config/openstack/clouds.yaml`
or system-wide: `/etc/openstack/clouds.yaml`.

Information in your homedir, if it exists, takes precedence.

Full docs on `clouds.yaml` are at
https://docs.openstack.org/developer/os-client-config/

What about Mac and Windows?
===========================

`USER_CONFIG_DIR` is different on Linux, OSX and Windows.

* Linux: `~/.config/openstack`
* OSX: `~/Library/Application Support/openstack`
* Windows: `C:\\Users\\USERNAME\\AppData\\Local\\OpenStack\\openstack`

`SITE_CONFIG_DIR` is different on Linux, OSX and Windows.

* Linux: `/etc/openstack`
* OSX: `/Library/Application Support/openstack`
* Windows: `C:\\ProgramData\\OpenStack\\openstack`

Only for Ansible
================

/etc/ansible/clouds.yaml

Config Terminology
==================

For multi-cloud, think of two types:

* `profile` - Facts about the `cloud` that are true for everyone
* `cloud` - Information specific to a given `user`

Remember your Execution Context!
================================

* ansible executes code on remote systems
* clouds.yaml needs to be on the host where the modules run
* auth information can be passed to modules directly
* other config (currently) MUST go in `clouds.yaml`
* **TODO**: Expose ability to pass entire cloud config

basic clouds.yaml for the example code
======================================

Simple example of a clouds.yaml

* Config for a named `cloud` "my-citycloud"
* Reference a well-known "named" profile: `citycloud`
* `os-client-config` has a built-in list of profiles at
  https://docs.openstack.org/developer/os-client-config/vendor-support.html
* Vendor profiles contain various advanced config
* `cloud` name can match `profile` name (using different names for clarity)

.. code:: yaml

  clouds:
    my-citycloud:
      profile: citycloud
      auth:
        username: mordred
        project_id: 65222a4d09ea4c68934fa1028c77f394
        user_domain_id: d0919bd5e8d74e49adf0e145807ffc38
        project_domain_id: d0919bd5e8d74e49adf0e145807ffc38

Where's the password?

secure.yaml
===========

* Optional additional file just like `clouds.yaml`
* Values overlaid on `clouds.yaml`
* Useful if you want to protect secrets more stringently

Example secure.yaml
===================

* No, my password isn't XXXXXXXX
* `cloud` name should match `clouds.yaml`
* Optional - I actually keep mine in my `clouds.yaml`

.. code:: yaml

  clouds:
    my-citycloud:
      auth:
        password: XXXXXXXX

more clouds.yaml
================

More information can be provided.

* Use v3 of the `identity` API - even if others are present
* Use `https://image-ca-ymq-1.vexxhost.net/v2` for `image` API
  instead of what's in the catalog

.. code:: yaml

    my-vexxhost:
      identity_api_version: 3
      image_endpoint_override: https://image-ca-ymq-1.vexxhost.net/v2
      profile: vexxhost
      auth:
        user_domain_id: default
        project_domain_id: default
        project_name: d8af8a8f-a573-48e6-898a-af333b970a2d
        username: 0b8c435b-cc4d-4e05-8a47-a2ada0539af1

Much more complex clouds.yaml example
=====================================

* Not using a profile - all settings included
* In the `ams01` `region` there are two networks with undiscoverable qualities
* Each one are labeled here so choices can be made
* Any of the settings can be specific to a `region` if needed
* `region` settings override `cloud` settings
* `cloud` does not support `floating-ips`

.. code:: yaml

    my-internap:
      auth:
        auth_url: https://identity.api.cloud.iweb.com
        username: api-55f9a00fb2619
        project_name: inap-17037
      identity_api_version: 3
      floating_ip_source: None
      regions:
      - name: ams01
        values:
          networks:
          - name: inap-17037-WAN1654
            routes_externally: true
            default_interface: true
          - name: inap-17037-LAN3631
            routes_externally: false

Extra Variables to Control Inventory Behavior
=============================================

* expand_hostvars - whether to make extra API calls to fill out additional
                    information about each server
* use_hostnames - changes the behavior from registering every host with its
                  UUID and making a group of its hostname to only doing this
                  if the hostname in question has more than one server
* fail_on_errors - causes the inventory to fail and return no hosts if one
                   cloud has failed

.. code:: yaml

  ansible:
    use_hostnames: False
    expand_hostvars: True
    fail_on_errors: True

Test Your Config
================

.. code:: yaml

  ---
  - hosts: localhost
    connection: local
    gather_facts: true
    tasks:
    - os_auth:
        cloud: '{{ item.cloud }}'
        region_name: '{{ item.region }}'
      with_items:
      - cloud: my-vexxhost
        region: ca-ymq-1
      - cloud: my-citycloud
        region: Buf1
      - cloud: my-internap
        region: ams01

More Interesting
================

.. code:: yaml

  ---
  - hosts: localhost
    connection: local
    gather_facts: true
    tasks:
    - os_server:
        name: 'my-server'
        cloud: '{{ item.cloud }}'
        region_name: '{{ item.region }}'
        image: '{{ item.image }}'
        flavor: '{{ item.flavor }}'
        auto_ip: true
      with_items:
      - cloud: my-vexxhost
        region: ca-ymq-1
        image: Ubuntu 16.04.1 LTS [2017-03-03]
        flavor: v1-standard-4
      - cloud: my-citycloud
        region: Buf1
        image: Ubuntu 16.04 Xenial Xerus
        flavor: 4C-4GB-100GB
      - cloud: my-internap
        region: ams01
        image: Ubuntu 16.04 LTS (Xenial Xerus)
        flavor: A1.4

Check That There is an Inventory
================================

.. code:: bash
  python ~/src/github.com/ansible/ansible/contrib/inventory/openstack.py --list

Cleanup After Ourselves
=======================

.. code:: yaml

  ---
  - hosts: localhost
    connection: local
    gather_facts: true
    tasks:
    - os_server:
        cloud: '{{ item.cloud }}'
        region_name: '{{ item.region }}'
        name: my-server
        state: absent
      with_items:
      - cloud: my-vexxhost
        region: ca-ymq-1
      - cloud: my-citycloud
        region: Buf1
      - cloud: my-internap
        region: ams01

Check out Ansible Cloud Launcher
================================

https://git.openstack.org/cgit/openstack/ansible-role-cloud-launcher

* Role for launching resources on an OpenStack Cloud

Check out Linch-pin
===================

http://linch-pin.readthedocs.io/en/develop/

* From our friends in CentOS

::
  Linch-pin provides a collection of Ansible playbooks for provisioning,
  decommissioning, and managing resources across multiple infrastructures. The
  main goal of linch-pin is to facilitate provisioning and orchestration of
  resources in a multi-cloud environment through a topology file.
