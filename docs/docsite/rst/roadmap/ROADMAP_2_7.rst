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


Cleaning Duty
-------------

- Drop Py2.6 for controllers  `Docs PR #42971 <https://github.com/ansible/ansible/pull/42971>`_ and
  `issue #42972 <https://github.com/ansible/ansible/issues/42972>`_
- Remove dependency on simplejson `issue #42761 <https://github.com/ansible/ansible/issues/42761>`_


Engine Improvements
-------------------

- Make ``become`` plugin based. `pr #38861 <https://github.com/ansible/ansible/pull/38861>`_
- Introduce a ``live`` keyword to provide modules the ability to push intermediate (live) updates `pr #13620 <https://github.com/ansible/ansible/pull/13620>`_
- Add content_path for mazer installed content `pr #42867 <https://github.com/ansible/ansible/pull/42867/>`_
- Investigate what it will take to utilise the work performed by Mitogen maintainers. `pr #41749 <https://github.com/ansible/ansible/pull/41749>`_, `branch <https://github.com/jimi-c/ansible/tree/abadger-ansiballz-one-interpreter>`_ and talk to jimi-c
- Provide sane connection defaults by platform `ansible_platform` `proposal #77 <https://github.com/ansible/proposals/issues/77>`_
- Refactor connection/shell/action/terminal/become plugins to allow looser coupling and more mix-and-match behaviour.(nitzmahone)
- Investigate performance improvements in using threads as opposed to forks `branch from jimi-c
  <https://github.com/ansible/ansible/tree/threading_plus_forking>`_
- Jinja native types will allow for users to render a Python native type. `pr #32738 <https://github.com/ansible/ansible/pull/32738>`_


Core Modules
------------

- Include feature changes and improvements

  - Create new argument ``apply`` that will allow for included tasks to inherit explicitly provided attributes. `pr #39236 <https://github.com/ansible/ansible/pull/39236>`_
  - Create "private" functionality for allowing vars/default sot be exposed outside of roles. `pr #41330 <https://github.com/ansible/ansible/pull/41330>`_

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
* RDS instance and snapshot modules `pr #39994 <https://github.com/ansible/ansible/pull/39994>`_ `issue #19524 <https://github.com/ansible/ansible/issues/19524>`_
* Diff mode improvements for cloud modules `pr #37212 <https://github.com/ansible/ansible/pull/37212>`_

Azure
=====

* Azure inventory plugin `issue #42769 <https://github.com/ansible/ansible/issues/42769>`__
* Azure stack support for modules `project tracker <https://github.com/nitzmahone/ansible/projects/2>`__


Network
-------

General
=======

* Refactor the APIs in cliconf (`issue #39056 <https://github.com/ansible/ansible/issues/39056>`_) and netconf (`issue #39160 <https://github.com/ansible/ansible/issues/39160>`_) plugins so that they have a uniform signature across supported network platforms.

Modules
=======

* New ``cli_config`` module `issue #39228 <https://github.com/ansible/ansible/issues/39228>`_
* New ``cli_command`` module `issue #39284 <https://github.com/ansible/ansible/issues/39284>`_
* Refactor ``netconf_config`` module to add additional functionality. `proposal #104 <https://github.com/ansible/proposals/issues/104>`_

Windows
-------

General
=======

* Investigate the cause of WinRM HTTPS read timeouts `issue #41145 <https://github.com/ansible/ansible/issues/41145>`__
* WinRM connection persistence (improves performance) `pr #41729 <https://github.com/ansible/ansible/pull/41729>`__
* Experiment with OpenSSH + powershell `pr #33074 <https://github.com/ansible/ansible/pull/33074>`_

Modules
=======

* `win_domain` and `win_domain_controller` action wrappers `issue #42764 <https://github.com/ansible/ansible/issues/42764>`__
* Add link to `win_file` `issue #43060 <https://github.com/ansible/ansible/issues/43060>`__
* Hostname change support for `win_domain` and `win_domain_controller` `issue #42768 <https://github.com/ansible/ansible/issues/42768>`__
