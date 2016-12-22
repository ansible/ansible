****************
Ansible by Red Hat,  Core 2.3
****************
**********************
Target: February/March 2017
**********************

- **General Comments from the Core Team**

  - The 2.3 Ansible Core is just a little different than the past two major releases we've done.  In addition to feature work, we're using part of the time for this release to reduce some of our backlog in other areas than pure development.
  - *Administration:* Clean up our GitHub repos and move to one repo so that contributions, tickets, submissions, etc are centralized and easier for both the community and the Core Team to manage.
    - *Metadata:* Move to a Metadata based system for modules.  This has been discussed here: https://github.com/ansible/proposals/blob/master/modules-management.md
  - *Documentation:* We're aware that Docs have issues.  Scott Butler, aka Dharmabumstead will be leading the charge on how he and we as a community can clean them up.
  - *Backlog & Stability:* We're spending some of the cycles for 2.3 trying to reduce our ticket/PR backlog, and clean up some particular areas of the project that the community has expressed particular frustrations about.
  - *Python 3:* The community and Toshio have done TONS of work getting Python 3 working.  Still more to go...
  - *Features:* We still have some cool stuff coming.  Check it out below.  For people on the Networking side of the world, the Persistent Connection Manager will be a *huge* feature and performance gain.


- **Repo Merge**

  - Script that a submitter can run to migrate their PR
  - Script that a committer can run to fork a PR and then merge to ansible/ansible
  - Move all the issues (remove old ones that can be removed)
  - Enhance ansibullbot to accommodate the changes (jctanner)
  
- **Metadata**

  - Add metadata to the modules we ship
  - Write code to use metadata in docs
  - If needed for python2/3 write code to use metadata in module_common or pluginloader
  
- **Documentation**
  
  - Update developing_modules
  - Set up rst skeleton for module_utils docs.
  - Plugin development docs
  - Speed up `make webdocs` https://github.com/ansible/ansible/issues/17406  (stretch)
  
- **Windows platform** (nitzmahone)
  
  - Pipelining support
  - Become support
  - Integrated kerberos ticket management (via ansible_user/ansible_password)
  - Switch PS input encoding to BOM-less UTF8
  - Server 2016 support/testing (now RTM’d)
  - Modularize Windows module_utils (allow N files)
  - Declarative argspec for PS / .NET
  - Kerberos encryption (via notting, pywinrm/requests_kerberos/pykerberos)
  - Fix plugin-specific connection var lookup/delegation (either registered explicitly by plugins or ansible_(plugin)_*)

- **Windows modules** (nitzmahone)

  - win_domain module
  - win_domain_membership module
  - win_domain_controller module
  - win_dns_client module
  - win_wait_for module
  - win_disk_image module
  - Updates to win_chocolatey, adopt to core (stretch)
  - Updates/rewrite to win_unzip, adopt to core (stretch)
  - Updates to win_updates, adopt to core (stretch)
  - Updates to win_package, adopt to core (+ deprecate win_msi)
  
- **Azure modules** (nitzmahone/mattclay)

  - Ensure Azure SDK rc6/RTM work
  - Move tests from ansible/azure_rm repo to ansible/ansible
  - Update/enhance tests
  - Expose endpoint overrides (support AzureChinaCloud, Azure Stack)
  - Get Azure tests running in CI (stretch, depends on availability of sponsored account)
  - azure_rm_loadbalancer module (stretch)
  
- **Networking**

  - Code stability and tidy up
  - Extend testing
  - User facing documentation
  - Persistent connection manager
  - Netconf/YANG implementation (only feature)
  - Deferred from 2.2: Network facts modules (sros)

- **Python3**

  - For 2.3:
  
    - We want all tests to pass (majority do but there’s 10-20 that still need fixes)
    - If users report bugs on python3, these should be fixed and will prioritize our work on porting other modules.
  - Still have to solve the python3-only and python2-only modules.  Thinking of doing this via metadata.  Will mean we have to use metadata at the module_common level.  Will also mean we don’t support py2-only or py3-only old style python modules. 
  - Note: Most of the currently tested ansible features now run.  But there’s still a lot of code that’s untested.

- **Testing and CI** (mattclay)  

  - *Static Code Analysis:* Create custom pylint extensions to automate detection of common Ansible specific issues reported during code review. Automate feedback on PRs for new code only to avoid noise from existing code which does not pass.
  - *Test Reliability:* Eliminate transient test failures by fixing unreliable tests. Reduce network dependencies by moving network resources into httptester.
  - *Enable Remaining Tests:* Implement fixes for OS X, FreeBSD and Python 3 to enable the remaining blacklisted tests for CI.
  - *Windows Server 2016:* Add Windows Server 2016 to CI when official AMIs become available.
  - *Repository Consolidation:* Update CI to maintain and improve upon existing functionality after repository consolidation.

- **Amazon resources** (ryansb)

  - Refactor ec2.py (but first, better testing)
  - ELB version 2
  - Multifactor authentication support (STS feature, affects all modules)
  - CloudFormation YAML, cross-stack reference, and roles support
  - ECS module refactor
  - AWS module unit testing w/ placebo (boto3 only)

- **Plugin Loader**

  - Add module_utils to the plugin loader (feature)
  - Split plugin loader: Plugin_search, plugin_loader (modules only use first) (Stretch goal)
  - Add a ‘ansible-ssh’ convenience and debugging tool
  
    - Tool to invoke an interactive ssh to a host with the same args/env/config that ansible would.
    - There are at least three external versions
    
      - https://github.com/2ndQuadrant/ansible-ssh
      - https://github.com/haad/ansible-ssh
      - https://github.com/mlvnd/ansible-ssh
