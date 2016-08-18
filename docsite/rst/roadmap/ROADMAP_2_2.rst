****************
Ansible Core 2.2
****************
**********************
Target: September 2016
**********************
- **Docker** (lead by Chris Houseknecht)

  - Docker_network
  - Docker_volume
  - Docker_file
  - Openshift:  oso_deployment, oso_route, oso_service, oso_login (...and possibly others. These are modules being developed to support `ansible-container <https://github.com/ansible/ansible-container>`_.)
  - Kubernetes: kube_deployment, kube_service, kube_login (...and possibly others. These too are modules being developed to support `ansible-container <https://github.com/ansible/ansible-container>`_)

- **Extras split from Core** (Team, Community, lead by Jason M and Jimi-c) (Targeting 2.2, could move into 2.3).
    Targeted towards the 2.2 release or shortly after, we are planning on splitting Extras out of the “Ansible Core” project.  That means that modules that are shipped with Ansible by default are **only** the modules in ansibl-modules-core.  Ansible extras will become a separate project, managed by the community standard.  Over the next few months we’re going to have a lot of work to do on getting all of the modules in the right places for this to work.

  - Create proposal (Jason or Jimi)
  - Review modules for correct location (extras v core)
  - Extras is a completely different package (does not install with ansible)
  - Library dependencies
  - Decide and implement release schedules between Ansible Core and Extras to ensure compatibility and longevity for modules and versions of Ansible.

- **Tweaks/Fixes**

  - Add the ability to set_fact to deal with updating arrays and hashes (Jimi)
  - Connection handling stuff. (Toshio K. and Brian C.): This is a stretch goal for 2.2.  It may go into 2.3

    - Change connection polling to avoid resource limitations, see `<https://github.com/ansible/ansible/issues/14143>`_
    - `<https://docs.python.org/3/library/selectors.html#module-selectors>`_
    - Code: https://github.com/kai11/ansible/blob/fix/select_fd_out_of_range_wip/lib/ansible/plugins/connection/ssh.py

- **Cloud Modules** (Ryan Brown)

  - AWS

    - Pagination for all AWS modules (generic pagination exists, but isn’t used everywhere)
    - Refactoring ec2.py to be more digestible
    - Fix inconsistencies with different authentication methods (STS, environment creds, ~/.aws/credentials)
    - Ryan Brown and Robyn Bergeron work on bug/PR triage to reduce backlog
  - Google (Ryan Brown and Tom Melendez)

    - Add support for Google Cloud DNS
    - Support restoring instances from snapshots
    - Improved handling of scratch disks on instances
  - External OpenStack (Stretch goal for this release)

    - Ryan with some help from David Shrewsbury (Zuul/Openstack at RedHat).
    - Support Heat stack resources
    - Support LBaaS load balancers
  - Azure load balancer: Feature parity for AWS ELB (Stretch Goal)

- **VMware** (Brian, Jtanner)

  - *module/inventory script: port to pyvmomi (jtanner, bcoca)*
    **done:** https://github.com/ansible/ansible/pull/15967
  - *inventory script: allow filtering ala ec2 (jtanner) (undergoing PR process)*
    **done:** https://github.com/ansible/ansible/pull/15967

  - vsphere: feature parity with whereismyjetpack and viasat modules 

- **Windows platform feature parity** (Matt D)

  - PS module API (mirror Python module API where appropriate). Note: We don’t necessarily like the current python module API (AnsibleModule is a huge class with many unrelated utility functions.  Maybe we should redesign both at the same time?)
  - Environment keyword support 
  - win_shell/win_command
  - Async support 
  - (stretch goal) Pipelining 

- **Windows-specific enhancements** (Matt D)

  - Multiple Kerberos credential support (done, shepherd fix to pykerberos)
  - Server 2016 testing/fixes 
  - (stretch goal) Nano Server connection + module_utils working
  - (stretch goal) Encrypted kerberos support in pywinrm 

- **Network** (Nate C/Peter S)

  - Unify NetworkModules (module_utils/network.py) as much as possible 
  - Add support for config diff and replace on supported platforms (2 weeks)
  - Network facts modules 
  - Support for VyOS network operating system
  - Add support for NetConf / RestConf for IOS/XE
  - Quagga modules 
  - Bird modules (stretch)
  - GoBGP modules (stretch)
  - Support for Dell Networking operating systems (OS9, OS6, OS10)

- **Implement ‘role revamp’ proposal to give users more control on role/task execution (Brian) **

  - **https://github.com/ansible/proposals/blob/master/roles_revamp.md**

- **Vault** (Jtanner/Adrian)

  - *Extend ‘transparent vault file usage’ to other action plugins other than 'copy'(https://github.com/ansible/ansible/issues/7298)*
    **done:** https://github.com/ansible/ansible/pull/16957
  - Add ‘per variable’ vault support (!vault YAML directive, existing PR already) https://github.com/ansible/ansible/issues/13287 https://github.com/ansible/ansible/issues/14721
  - Add vault/unvault filters https://github.com/ansible/ansible/issues/12087 (deferred to 2.3)
  - Add vault support to lookups (likely deferred to 2.3 or until lookup plugins are revamped)
  - Allow for multiple vault secrets https://github.com/ansible/ansible/issues/13243
  - Config option to turn ‘unvaulting’ failures into warnings https://github.com/ansible/ansible/issues/13244

- **Python3** (Toshio)
    A note here from Jason M: Getting to complete, tested Python 3 is both a critical task and one that has so much work, and so many moving parts that we don’t expect this to be complete by the 2.2 release.  Toshio will lead this overall effort.

  - RHEL8 is coming which has no python2 in default install.  Ubuntu (non-LTS) already ships without python2.  These considerations make this high priority.
  - Ansible users are getting restless: https://groups.google.com/forum/#!topic/ansible-project/DUKzTho3OCI
  - This is probably going to take multiple releases to complete.
  - Side work to do: Figure out best ways to run unit-tests on modules.  Start unit-testing modules.  This is going to become important so we don’t regress python3 or python2.4 support in modules  (Going to largely punt on this for 2.2.  Sounds like Matt Clay is working on building us a testing foundation for the first half of 2.2 development so we’ll re-evaluate towards the middle of the dev cycle).
  - Goals for 2.2:  

    - Controller-side code can run on python3 [but may not work in practice as targeting localhost presently uses the python that runs /bin/ansible instead of defaulting to /usr/bin/python like any other target]  

      - Bcoca suggests: If we’re running controller under sys.version_info[0] &gt;= 3, try to detect a python2 to set implicit localhost to instead of using sys.executable as workaround for modules not working with py3 yet. 
      - We’ll have to make some decisions about some of our dependencies 

        - The base deps in setup.py are ported: ['paramiko', 'jinja2', "PyYAML", 'setuptools', 'pycrypto &gt;= 2.6']
        - Python-keyczar and python-six are additional deps in the rpm spec file.  Six is ported but keyczar is not. (removing keyczar when we drop accelerate for 2.3)  print deprecation in 2.1.

    - Module_utils ported to dual python3/python2(2.4 for much of it, python2.6 for specific things)
    - Add module_utils files to help port -- copy of the six library (v1.4.1 for python2.4 compat), unicode helpers from ansible.utils.
    - More unit tests of module_utils
    - A few basic modules ported to python3

      - Stat module best example module since it’s essential.

    - Python3 integration tests -- jimi’s idea was mark some distributions as able to fail and have them run via run_tests.sh with python3 (Fedora-rawhide, latest ubuntu?) 
    - Some setup.py/packaging tweaks to make it easier for users to test with py2 and py3  (ansible-playbook-py2 and py3 installed in bin?)

  - Goals for 2.3:

    - Go for low hanging fruit: modules that are already python2.6+ may be easy to port to python3.

      - Unfortunately, we may also have the least automated testing on these (as a large number of these are cloud modules)
      - Will need to figure out how to organize “works on python3” into a cohesive set.

    - Increase number of essential modules that have been ported.  Package managers, url fetching, etc.

- **Infrastructure Buildout and Changes** (Matt Clay)
    Another note from Jason M: A lot of this work is to ease the burden of CI, CI performance, increase our testing coverage and all of that sort of thing.  It’s not necessarily feature work, but it’s \*\*critical\*\* to growing our product and our ability to get community changes in more securely and quickly.

  - **CI Performance**
      Reduce time spent waiting on CI for PRs. Combination of optimizing existing Travis setup and offloading work to other services. Will be impacted by available budget.
      **Done:** Most tests have been migrated from Travis to Shippable.
  - **Core Module Test Organization**
      Relocate core module tests to ansible-modules-core to encourage inclusion of tests in core module PRs.
  - **Documentation**
      Expand documentation on setting up a development and test environment, as well as writing tests. The goal is to ease development for new contributors and encourage more testing, particularly with module contributions.
  - **Test Coverage**
      Expand test coverage, particularly for CI. Being testing, this is open ended. Will be impacted by available budget.
    - Python 3 - Run integration tests using Python 3 on CI with tagging for those which should pass, so we can track progress and detect regressions.
    - Windows - Create framework for running Windows integration tests, ideally both locally and on CI.
      **Done:** Windows integration tests now run on Shippable.
    - FreeBSD - Include FreeBSD in CI coverage. Not originally on the roadmap, this is an intermediary step for CI coverage for OS X.
      **Done:** FreeBSD integration tests now run on Shippable.
    - OS X - Include OS X in CI coverage.
