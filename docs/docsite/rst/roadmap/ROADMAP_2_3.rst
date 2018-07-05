===========
Ansible 2.3
===========
**Target: Mid April 2017**

.. contents:: Topics

General Comments from the Core Team
-----------------------------------

- The 2.3 Ansible Core is just a little different than the past two major releases we've done.  In addition to feature work, we're using part of the time for this release to reduce some of our backlog in other areas than pure development.
- *Administration:* Clean up our GitHub repos and move to one repo so that contributions, tickets, submissions, etc are centralized and easier for both the community and the Core Team to manage.
- *Metadata:* Move to a Metadata based system for modules.  This has been discussed here: https://github.com/ansible/proposals/blob/master/modules-management.md
- *Documentation:* We're aware that Docs have issues.  Scott Butler, aka Dharmabumstead will be leading the charge on how he and we as a community can clean them up.
- *Backlog & Stability:* We're spending some of the cycles for 2.3 trying to reduce our ticket/PR backlog, and clean up some particular areas of the project that the community has expressed particular frustrations about.
- *Python 3:* The community and Toshio have done TONS of work getting Python 3 working.  Still more to go...
- *Features:* We still have some cool stuff coming.  Check it out below.  For people on the Networking side of the world, the Persistent Connection Manager will be a *huge* feature and performance gain.

Repo Merge
----------
- Script that a submitter can run to migrate their PR **(done)**
- Script that a committer can run to fork a PR and then merge to ansible/ansible **(mostly done)**
- Move all the issues (remove old ones that can be removed) **(done)**
- Enhance ansibullbot to accommodate the changes (jctanner) **(in progress, going well)**

Metadata
--------
- Add metadata to the modules we ship **(done)**
- Write code to use metadata in docs **(done)**
- If needed for python2/3 write code to use metadata in module_common or pluginloader **(not needed)**

Documentation
-------------
- Update developing_modules **(in progress, will continue in 2.4)**
- Set up rst skeleton for module_utils docs.
- Plugin development docs
- Speed up `make webdocs` https://github.com/ansible/ansible/issues/17406   **(done)**

Windows
-------
Lead by nitzmahone

- **Platform**

  - Pipelining support **(done)**
  - Become support **(done/experimental)**
  - Integrated kerberos ticket management (via ansible_user/ansible_password) **(done)**
  - Switch PS input encoding to BOM-less UTF8 **(done)**
  - Server 2016 support/testing (now RTM'd) **(partial)**
  - Modularize Windows module_utils (allow N files) **(partial)**
  - Declarative argspec for PS / .NET **(bumped to 2.4)**
  - Kerberos encryption (via notting, pywinrm/requests_kerberos/pykerberos) **(in progress, available in pywinrm post 2.3 release)**
  - Fix plugin-specific connection var lookup/delegation (either registered explicitly by plugins or ansible_(plugin)_*) **(bumped to 2.4)**

- **Modules**

  - win_domain module **(done)**
  - win_domain_membership module **(done)**
  - win_domain_controller module **(done)**
  - win_dns_client module **(done)**
  - win_wait_for module
  - win_disk_image module **(done)**
  - Updates to win_chocolatey, adopt to core (stretch) **(bump to 2.4)**
  - Updates/rewrite to win_unzip, adopt to core (stretch) **(bump to 2.4)**
  - Updates to win_updates, adopt to core (stretch) **(bump to 2.4)**
  - Updates to win_package, adopt to core (+ deprecate win_msi) (stretch) **(bump to 2.4)**

Azure
-----
Lead by nitzmahone, mattclay

- Ensure Azure SDK rc6/RTM work **(done)**
- Move tests from ansible/azure_rm repo to ansible/ansible **(bump to 2.4, no CI resources)**
- Update/enhance tests **(bump to 2.4, no CI resources)**
- Expose endpoint overrides (support AzureChinaCloud, Azure Stack) **(bump to 2.4)**
- Get Azure tests running in CI (stretch, depends on availability of sponsored account) **(bump to 2.4, no CI resources)**
- azure_rm_loadbalancer module (stretch) **(bump to 2.4)**

Networking
----------
- Code stability and tidy up **(done)**
- Extend testing **(done)**
- User facing documentation
- Persistent connection manager **(done)**
- Netconf/YANG implementation (only feature) **(done)**
- Deferred from 2.2: Network facts modules (sros)

Python3
-------

- For 2.3:

  - We want all tests to pass

    - Just the mercurial tests left because we haven't created an image with
      both python2 and python3 to test it on yet.
    - Check by doing ``grep skip/python3 test/integration/targets/*/aliases``

  - If users report bugs on python3, these should be fixed and will prioritize our work on porting other modules.

- Still have to solve the python3-only and python2-only modules.  Thinking of doing this via metadata.  Will mean we have to use metadata at the module_common level.  Will also mean we don't support py2-only or py3-only old style python modules.
- Note: Most of the currently tested ansible features now run.  But there's still a lot of code that's untested.

Testing and CI
--------------
Lead by mattclay

- *Static Code Analysis:* Create custom pylint extensions to automate detection of common Ansible specific issues reported during code review. Automate feedback on PRs for new code only to avoid noise from existing code which does not pass.

  **Ongoing:** Some static code analysis is now part of the CI process:

  - pep8 is now being run by CI, although not all PEP 8 rules are being enforced.
  - pylint is now being run by CI, but currently only on the ansible-test portion of codebase.

- *Test Reliability:* Eliminate transient test failures by fixing unreliable tests. Reduce network dependencies by moving network resources into httptester.

  **Ongoing:** Many of the frequent sources of test instability have been resolved. However, more work still remains.

  Some new issues have also appeared, which are currently being worked on.

- *Enable Remaining Tests:* Implement fixes for macOS, FreeBSD and Python 3 to enable the remaining blacklisted tests for CI.

  **Ongoing:** More tests have been enabled for macOS, FreeBSD and Python 3. However, work still remains to enable more tests.

- *Windows Server 2016:* Add Windows Server 2016 to CI when official AMIs become available.

  **Delayed:** Integration tests pass on Windows Server 2016. However, due to intermittent WinRM issues, the tests have been disabled.

  Once the issues with WinRM have been resolved, the tests will be re-enabled.

- *Repository Consolidation:* Update CI to maintain and improve upon existing functionality after repository consolidation.

  **Done:** A new test runner, ansible-test, has been deployed to manage CI jobs on Shippable.

  Tests executed on PRs are based on the changes made in the PR, for example:

  - Changes to a module will only run tests appropriate for that module.
  - Changes to Windows modules or the Windows connection plugin run tests on Windows.
  - Changes to network modules run tests on the appropriate virtual network device (currently supporting VyOS and IOS).

  Tests executed on merges are based on changes since the last successful merge test.

Amazon
------
Lead by ryansb

- Improve ec2.py integration tests **(partial, more to do in 2.4)**
- ELB version 2 **(pushed - needs_revision)** `PR <https://github.com/ansible/ansible/pull/19491>`_
- CloudFormation YAML, cross-stack reference, and roles support **(done)**
- ECS module refactor **(done)**
- AWS module unit testing w/ placebo (boto3 only) **(pushed 2.4)**

Plugin Loader
-------------
- Add module_utils to the plugin loader (feature) [done]
- Split plugin loader: Plugin_search, plugin_loader (modules only use first) [pushed to 2.4]

ansible-ssh
-----------
- Add a 'ansible-ssh' convenience and debugging tool (will slip to 2.4)
- Tool to invoke an interactive ssh to a host with the same args/env/config that ansible would.
- There are at least three external versions

  - https://github.com/2ndQuadrant/ansible-ssh
  - https://github.com/haad/ansible-ssh
  - https://github.com/mlvnd/ansible-ssh
