================
Ansible Core 2.1
================
**Target: April**

.. contents:: Topics

Windows
-------
- General

  - Figuring out privilege escalation (runas w/ username/password)
  - Implement kerberos encryption over http
  - pywinrm conversion to requests (Some mess here on pywinrm/requests. will need docs etc.)
  - NTLM support

- Modules

  - Finish cleaning up tests and support for post-beta release
  - Strict mode cleanup (one module in core)
  - Domain user/group management
  - Finish win_host and win_rm in the domain/workgroup modules.

    - Close 2 existing PRs (These were deemed insufficient)

  - Replicate python module API in PS/C# (deprecate hodgepodge of stuff from module_utils/powershell.ps1)

Network
-------
- Cisco modules (ios, iosxr, nxos, iosxe)
- Arista modules (eos)
- Juniper modules (junos)
- OpenSwitch
- Cumulus
- Dell (os10) - At risk
- Netconf shared module
- Hooks for supporting Tower credentials

VMware
------
This one is a little at risk due to staffing. We're investigating some community maintainers and shifting some people at Ansible around, but it is a VERY high priority.

- vsphere\_guest brought to parity with other vmware modules (vs Viasat and 'whereismyjetpack' provided modules)
- VMware modules moved to official pyvmomi bindings
- VMware inventory script updates for pyvmomi, adding tagging support

Azure
-----
This is on hold until Microsoft swaps out the code generator on the Azure Python SDK, which may introduce breaking changes. We have basic modules working against all of these resources at this time. Could ship it against current SDK, but may break. Or should the version be pinned?)
- Minimal Azure coverage using new ARM api
- Resource Group
- Virtual Network
- Subnet
- Public IP
- Network Interface
- Storage Account
- Security Group
- Virtual Machine
- Update of inventory script to use new API, adding tagging support


Docker
------
- Start Docker module refactor
- Update to match current docker CLI capabilities
- Docker exec support

Cloud
-----
Upgrade other cloud modules or work with community maintainers to upgrade.  (In order)

- AWS (Community maintainers)
- Openstack (Community maintainers)
- Google (Google/Community)
- Digital Ocean (Community)

Ansiballz
---------
Renamed from Ziploader

- Write code to create the zipfile that gets passed across the wire to be run on the remote python
- Port most of the functionality in module\_utils to be usage in ansiballz instead
- Port a few essential modules to use ansiballz instead of module-replacer as proof of concept
- New modules will be able to use ansiballz.  Old modules will need to be ported in future releases (Some modules will not need porting but others will)
- Better testing of modules, caching of modules clientside(Have not yet arrived at an architecture for this that we like), better code sharing between ansible/ansible and modules
- ansiballz is a helpful building block for: python3 porting(high priority), better code sharing between modules(medium priority)
- ansiballz is a good idea before: enabling users to have custom module_utils directories

Diff-support
------------
Expand module diff support (already in progress in devel)

- Framework done. Need to add to modules, test etc.
- Coordinate with community to update their modules

Other
-----
Things being kicking down the road that we said we’d do

- NOT remerging core with ansible/ansible this release cycle

Community
---------
- Define the process/ETA for reviewing PR’s from community
- Publish better docs and how-tos for submitting code/features/fixes
