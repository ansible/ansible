===========
Ansible 2.7
===========

.. contents:: Topics

Release Schedule
----------------

Expected
========

- 2018-08-23 Core Freeze (Engine and Core Modules/Plugins)
- 2018-08-23 Alpha Release 1
- 2018-08-30 Community Freeze (Non-Core Modules/Plugins)
- 2018-08-30 Beta Release 1
- 2018-09-06 Release Candidate 1 (If needed)
- 2018-09-13 Release Candidate 2 (If needed)
- 2018-09-20 Release Candidate 3 (If needed)
- 2018-09-27 Release Candidate 4 (If needed)
- 2018-10-04 General Availability

Release Manager
---------------
Toshio Kuratomi (IRC: abadger1999; GitHub: @abadger)


Cleaning Duty
-------------

- Drop Py2.6 for controllers  `Docs PR #42971 <https://github.com/ansible/ansible/pull/42971>`_ and
  `issue #42972 <https://github.com/ansible/ansible/issues/42972>`_
- Remove dependency on simplejson `issue #42761 <https://github.com/ansible/ansible/issues/42761>`_


Engine Improvements
-------------------

- Performance improvement invoking Python modules `pr #41749 <https://github.com/ansible/ansible/pull/41749>`_
- Jinja native types will allow for users to render a Python native type. `pr #32738 <https://github.com/ansible/ansible/pull/32738>`_


Core Modules
------------

- Include feature changes and improvements

  - Create new argument ``apply`` that will allow for included tasks to inherit explicitly provided attributes. `pr #39236 <https://github.com/ansible/ansible/pull/39236>`_
  - Create "private" functionality for allowing vars/default to be exposed outside of roles. `pr #41330 <https://github.com/ansible/ansible/pull/41330>`_
- Provide a parameter for the ``template`` module to output to different encoding formats `pr
  #42171 <https://github.com/ansible/ansible/pull/42171>`_
- ``reboot`` module for Linux hosts (@samdoran) `pr #35205 <https://github.com/ansible/ansible/pull/35205>`_

Cloud Modules
-------------

General
=======
* Cloud auth plugin `proposal #24 <https://github.com/ansible/proposals/issues/24>`_

AWS
===
* Inventory plugin for RDS `pr #41919 <https://github.com/ansible/ansible/pull/41919>`_
* Count support for `ec2_instance`
* `aws_eks` module `pr #41183 <https://github.com/ansible/ansible/pull/41183>`_
* Cloudformation stack sets support (`PR#41669 <https://github.com/ansible/ansible/pull/41669>`_)
* RDS instance and snapshot modules `pr #39994 <https://github.com/ansible/ansible/pull/39994>`_ `pr #43789 <https://github.com/ansible/ansible/pull/43789>`_
* Diff mode improvements for cloud modules `pr #44533 <https://github.com/ansible/ansible/pull/44533>`_

Azure
=====

* Azure inventory plugin `issue #42769 <https://github.com/ansible/ansible/issues/42769>`__


Network
-------

General
=======

* Refactor the APIs in cliconf (`issue #39056 <https://github.com/ansible/ansible/issues/39056>`_) and netconf (`issue #39160 <https://github.com/ansible/ansible/issues/39160>`_) plugins so that they have a uniform signature across supported network platforms. **done**
  (`PR #41846 <https://github.com/ansible/ansible/pull/41846>`_) (`PR #43643 <https://github.com/ansible/ansible/pull/43643>`_) (`PR #43837 <https://github.com/ansible/ansible/pull/43837>`_)
  (`PR #43203 <https://github.com/ansible/ansible/pull/43203>`_) (`PR #42300 <https://github.com/ansible/ansible/pull/42300>`_) (`PR #44157 <https://github.com/ansible/ansible/pull/44157>`_)

Modules
=======

* New ``cli_config`` module `issue #39228 <https://github.com/ansible/ansible/issues/39228>`_ **done** `PR #42413 <https://github.com/ansible/ansible/pull/42413>`_.
* New ``cli_command`` module `issue #39284 <https://github.com/ansible/ansible/issues/39284>`_
* Refactor ``netconf_config`` module to add additional functionality. **done** `proposal #104 <https://github.com/ansible/proposals/issues/104>`_ (`PR #44379 <https://github.com/ansible/ansible/pull/44379>`_)

Windows
-------

General
=======

* Added new connection plugin that uses PSRP as the connection protocol `pr #41729 <https://github.com/ansible/ansible/pull/41729>`__

Modules
=======

* Revamp Chocolatey to fix bugs and support offline installation `pr #43013 <https://github.com/ansible/ansible/pull/43013>`_.
* Add Chocolatey modules that can manage the following Chocolatey features

    * `Sources <https://chocolatey.org/docs/commands-sources>`_ `pr #42790 <https://github.com/ansible/ansible/pull/42790>`_
    * `Features <https://chocolatey.org/docs/chocolatey-configuration#features>`_ `pr #42848 <https://github.com/ansible/ansible/pull/42848>`_
    * `Config <https://chocolatey.org/docs/chocolatey-configuration#config-settings>`_ `pr #42915 <h*ttps://github.com/ansible/ansible/pull/42915>`_
