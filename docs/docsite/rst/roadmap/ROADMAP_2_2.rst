===========
Ansible 2.2
===========
**Target: September 2016**

.. contents:: Topics

Docker
------
Lead by Chris Houseknecht

- Docker_network: **done**
- Docker_volume: Not in this release
- Docker_file: Not in this release.
- Openshift:  oso_deployment, oso_route, oso_service, oso_login (...and possibly others. These are modules being developed to support `ansible-container <https://github.com/ansible/ansible-container>`_.): Deferred for later release
- Kubernetes: kube_deployment, kube_service, kube_login (...and possibly others. These too are modules being developed to support `ansible-container <https://github.com/ansible/ansible-container>`_): Deferred for later release

Extras split from Core
----------------------
Lead by Jason M and Jimi-c (Targeting 2.2, could move into 2.3).

Targeted towards the 2.2 release or shortly after, we are planning on splitting Extras out of the "Ansible Core" project.  That means that modules that are shipped with Ansible by default are **only** the modules in ansibl-modules-core.  Ansible extras will become a separate project, managed by the community standard.  Over the next few months we're going to have a lot of work to do on getting all of the modules in the right places for this to work.

- Create proposal (Jason or Jimi)
- Review modules for correct location (extras v core)
- Extras is a completely different package (does not install with ansible)
- Library dependencies
- Decide and implement release schedules between Ansible Core and Extras to ensure compatibility and longevity for modules and versions of Ansible.

Tweaks/Fixes
------------
- Connection handling stuff. (Toshio K. and Brian C.): This is a stretch goal for 2.2.  **This work got pushed out**

  - Change connection polling to avoid resource limitations, see `<https://github.com/ansible/ansible/issues/14143>`_
  - `<https://docs.python.org/3/library/selectors.html#module-selectors>`_
  - Code: https://github.com/kai11/ansible/blob/fix/select_fd_out_of_range_wip/lib/ansible/plugins/connection/ssh.py


AWS
---
Lead by Ryan Brown

- Pagination for all AWS modules (generic pagination exists, but isn't used everywhere) (bumped to 2.3)
- Refactoring ec2.py to be more digestible (bumped to 2.3)
- Fix inconsistencies with different authentication methods (STS, environment creds, ~/.aws/credentials) (done)
- AWS Lambda modules (lambda_execute done, others pending)
- Ryan Brown and Robyn Bergeron work on bug/PR triage to reduce backlog (reduced - continuing to work on it)

Google
------
Lead by Ryan Brown and Tom Melendez

- Add support for Google Cloud DNS
- Add support for Google Cloud managed instance groups (done)
- Support restoring instances from snapshots
- Improved handling of scratch disks on instances (done)

OpenStack
---------
Lead by Ryan Brown

Stretch goal for this release

- Ryan with some help from David Shrewsbury (Zuul/Openstack at RedHat).
- Support Heat stack resources (done)
- Support LBaaS load balancers

Azure load balancer
-------------------
- Feature parity for AWS ELB (Stretch Goal)

VMware
------
Lead by Brian, Jtanner

- *module/inventory script: port to pyvmomi (jtanner, bcoca)*
  **done:** https://github.com/ansible/ansible/pull/15967
- *inventory script: allow filtering ala ec2 (jtanner) (undergoing PR process)*
  **done:** https://github.com/ansible/ansible/pull/15967
- vsphere: feature parity with whereismyjetpack and viasat modules 

Windows
-------
Lead by Matt D

- Feature parity

  - PS module API (mirror Python module API where appropriate). Note: We don't necessarily like the current python module API (AnsibleModule is a huge class with many unrelated utility functions.  Maybe we should redesign both at the same time?) (bumped to 2.3+ due to "moving target" uncertainty)
  - Environment keyword support (done)
  - win_shell/win_command (done)
  - Async support (done)
  - (stretch goal) Pipelining (bumped to 2.3+)

- Windows-specific enhancements

  - Multiple Kerberos credential support (done)
  - Server 2016 testing/fixes (done, awaiting next TP/RTM)
  - (stretch goal) Nano Server connection + module_utils working (bumped to 2.3)
  - (stretch goal) Encrypted kerberos support in pywinrm (bumped to 2.3)

Network
-------
Lead by Nate C, Peter S

- **Done:** Unify NetworkModules (module_utils/network.py) as much as possible 
- **Done:** Add support for config diff and replace on supported platforms (2 weeks)
- **Done:** Support for VyOS network operating system
- **Done:** Add support for RestConf for IOS/XE
- **Done:** Support for Dell Networking OS10
- **Done:** Add support for Nokia SR OS modules
- **Done:** Network facts modules (dellos, eos, ios, iosxr, junos, nxos, openswitch, vyos)
- **Deferred:** Network facts modules (cumulus, netvisor, sros)
- **Deferred:** Add support for NetConf for IOS/XE
- **Deferred:** (stretch goal) Quagga modules
- **Deferred:** (stretch goal) Bird modules
- **Deferred:** (stretch goal) GoBGP modules

Role revamp
-----------
- Implement 'role revamp' proposal to give users more control on role/task execution (Brian)

  - **https://github.com/ansible/proposals/blob/master/roles_revamp.md**

Vault
-----
Lead by Jtanner, Adrian

- *Extend 'transparent vault file usage' to other action plugins other than 'copy'(https://github.com/ansible/ansible/issues/7298)*
  **done:** https://github.com/ansible/ansible/pull/16957
- Add 'per variable' vault support (!vault YAML directive, existing PR already) https://github.com/ansible/ansible/issues/13287 https://github.com/ansible/ansible/issues/14721
- Add vault/unvault filters https://github.com/ansible/ansible/issues/12087 (deferred to 2.3)
- Add vault support to lookups (likely deferred to 2.3 or until lookup plugins are revamped)
- Allow for multiple vault secrets https://github.com/ansible/ansible/issues/13243
- Config option to turn 'unvaulting' failures into warnings https://github.com/ansible/ansible/issues/13244

Python3
-------
Lead by Toshio

A note here from Jason M: Getting to complete, tested Python 3 is both
a critical task and one that has so much work and so many moving parts
that we don't expect this to be complete by the 2.2 release.  Toshio will
lead this overall effort.

- Motivation:
  - Ubuntu LTS (16.04) already ships without python2.  RHEL8 is coming which is also expected to be python3 based.  These considerations make this high priority.
  - Ansible users are getting restless: https://groups.google.com/forum/#!topic/ansible-project/DUKzTho3OCI
  - This is probably going to take multiple releases to complete; need to get started now

- Baselines:
  - We're targeting Python-3.5 and above.

- Goals for 2.2:

  - Tech preview level of support
  - Controller-side code can run on Python3
  - Update: Essential features have been shown to work on Python3.
    Currently all unittests and all but three integration tests are
    passing on Python3.  Code has not been line-by-line audited so bugs
    remain but can be treated as bugs, not as massive, invasive new features.
  - Almost all of our deps have been ported:

    - The base deps in setup.py are ported: ['paramiko', 'jinja2', "PyYAML", 'setuptools', 'pycrypto &gt;= 2.6']
    - python-six from the rpm spec file has been ported
    - Python-keyczar from the rpm spec file is not.
    - Strategy: removing keyczar when we drop accelerate for 2.3. Print deprecation in 2.1.

  - Module_utils ported to dual python3/python2(2.4 for much of it, python2.6 for specific things)
    **Mostly done:**  Also not line-by-line audited but the unittests
    and integration tests do show that the most use functionality is working.
  - Add module_utils files to help port

    - Update: copy of the six library (v1.4.1 for python2.4 compat) and unicode helpers are here (ansible.module_utils._text.{to_bytes,to_text,to_native})
  - A few basic modules ported to python3

    - Stat module best example module since it's essential.
    - Update:

      - A handful of modules like stat have been line-by-line ported.  They should work reliably with few python3-specific bugs.  All but three integration tests pass which means that most essential modules are working to some extent on Python3.

        - The three failing tests are: service, hg, and uri.
        - Note, large swaths of the modules are not tested.  The status of
           these is unknown

  - All code should compile under Python3.
    - lib/ansible/* and all modules now compile under Python-3.5

  - Side work to do:
    - Figure out best ways to run unit-tests on modules.  Start unit-testing modules.  This is going to become important so we don't regress python3 or python2.4 support in modules  (Going to largely punt on this for 2.2.  Matt Clay is working on building us a testing foundation for the first half of 2.2 development so we'll re-evaluate towards the middle of the dev cycle).
    - More unit tests of module_utils
    - More integration tests.  Currently integration tests are the best way to test ansible modules so we have to rely on those.

  - Goals for 2.3:

    - Bugfixing, bugfixing, bugfixing.  We need community members to test,
      submit bugs, and add new unit and integration tests.  I'll have some
      time allocated both to review any Python3 bugfixes that they submit
      and to work on bug reports without PRs.  The overall goal is to make
      the things that people do in production with Ansible work on Python 3.

Infrastructure Buildout and Changes
-----------------------------------
Lead by Matt Clay

Another note from Jason M: A lot of this work is to ease the burden of CI, CI performance, increase our testing coverage and all of that sort of thing.  It's not necessarily feature work, but it's \*\*critical\*\* to growing our product and our ability to get community changes in more securely and quickly.

- **CI Performance**
  Reduce time spent waiting on CI for PRs. Combination of optimizing existing Travis setup and offloading work to other services. Will be impacted by available budget.

  **Done:** Most tests have been migrated from Travis to Shippable.

- **Core Module Test Organization**
  Relocate core module tests to ansible-modules-core to encourage inclusion of tests in core module PRs.

  **Deferred:** Relocation of core module tests has been deferred due to proposed changes in `modules management <https://github.com/ansible/proposals/blob/master/modules-management.md>`_.

- **Documentation**
  Expand documentation on setting up a development and test environment, as well as writing tests. The goal is to ease development for new contributors and encourage more testing, particularly with module contributions.
- **Test Coverage**

  - Expand test coverage, particularly for CI. Being testing, this is open ended. Will be impacted by available budget.

    **Done:** Module PRs now run integration tests for the module(s) being changed.

  - Python 3 - Run integration tests using Python 3 on CI with tagging for those which should pass, so we can track progress and detect regressions.

    **Done:** Integration tests now run on Shippable using a Ubuntu 16.04 docker image with only Python 3 installed.

  - Windows - Create framework for running Windows integration tests, ideally both locally and on CI.

    **Done:** Windows integration tests now run on Shippable.

  - FreeBSD - Include FreeBSD in CI coverage. Not originally on the roadmap, this is an intermediary step for CI coverage for macOS.

    **Done:** FreeBSD integration tests now run on Shippable.

  - macOS - Include macOS in CI coverage.

    **Done:** macOS integration tests now run on Shippable.
