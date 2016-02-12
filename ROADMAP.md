Roadmap For Ansible by RedHat
=============
This document is now the location for published Ansible Core roadmaps.     

The roadmap will be updated by version. Based on team and community feedback, an initial roadmap will be published for a major or minor version (2.0, 2.1).  Subminor versions will generally not have roadmaps published.

This is the first time Ansible has published this and asked for feedback in this manner.  So feedback on the roadmap and the new process is quite welcome.  The team is aiming for further transparency and better inclusion of both community desires and submissions.  

These roadmaps are the team's *best guess* roadmaps based on the Ansible team's experience and are also based on requests and feedback from the community.  There are things that may not make it on due to time constraints, lack of community maintainers, etc.  And there may be things that got missed, so each roadmap is published both as an idea of what is upcoming in Ansible, and as a medium for seeking further feedback from the community. Here are the good places for you to submit feedback:

  * Ansible's google-group: ansible-devel
  *  Ansible Fest conferences.  
  * IRC freenode channel: #ansible-devel (this one may have things lost in lots of conversation, so a caution).

2.1 Roadmap, Targeted for the End of April
==========
## Windows, General
* Figuring out privilege escalation (runas w/ username/password)
* Implement kerberos encryption over http
* pywinrm conversion to requests (Some mess here on pywinrm/requests. will need docs etc.)
* NTLM support

## Modules
* Windows
  * Finish cleaning up tests and support for post-beta release
  * Strict mode cleanup (one module in core)
  * Domain user/group management
  * Finish win\_host and win\_rm in the domain/workgroup modules. 
     * Close 2 existing PRs (These were deemed insufficient)
  * Replicate python module API in PS/C# (deprecate hodgepodge of stuff from module_utils/powershell.ps1)
* Network
  * Cisco modules (ios, iosxr, nxos, iosxe)
  * Arista modules (eos)
  * Juniper modules (junos)
  * OpenSwitch
  * Cumulus
  * Dell (os10) - At risk
  * Netconf shared module
  * Hooks for supporting Tower credentials
* VMware (This one is a little at risk due to staffing. We're investigating some community maintainers and shifting some people at Ansible around, but it is a VERY high priority).
  * vsphere\_guest brought to parity with other vmware modules (vs Viasat and 'whereismyjetpack' provided modules)
  * VMware modules moved to official pyvmomi bindings
  * VMware inventory script updates for pyvmomi, adding tagging support
* Azure (Notes: This is on hold until Microsoft swaps out the code generator on the Azure Python SDK, which may introduce breaking changes. We have basic modules working against all of these resources at this time. Could ship it against current SDK, but may break. Or should the version be pinned?)
  * Minimal Azure coverage using new ARM api
  * Resource Group
  * Virtual Network
  * Subnet
  * Public IP
  * Network Interface
  * Storage Account
  * Security Group
  * Virtual Machine
  * Update of inventory script to use new API, adding tagging support
* Docker:
  * Start Docker module refactor
  * Update to match current docker CLI capabilities
  * Docker exec support
* Upgrade other cloud modules or work with community maintainers to upgrade.  (In order)
  * AWS (Community maintainers)
  * Openstack (Community maintainers)
  * Google (Google/Community) 
   * Digital Ocean (Community)
* Ziploader: 
  * Write code to create the zipfile that gets passed across the wire to be run on the remote python  
  * Port most of the functionality in module\_utils to be usage in ziploader instead
  * Port a few essential modules to use ziploader instead of module-replacer as proof of concept  
  *  New modules will be able to use ziploader.  Old modules will need to be ported in future releases (Some modules will not need porting but others will)
  * Better testing of modules, caching of modules clientside(Have not yet arrived at an architecture for this that we like), better code sharing between ansible/ansible and modules
  * ziploader is a helpful building block for: python3 porting(high priority), better code sharing between modules(medium priority)
  * ziploader is a good idea before: enabling users to have custom module_utils directories
* Expand module diff support (already in progress in devel)
  * Framework done. Need to add to modules, test etc. 
  * Coordinate with community to update their modules 
* Things being kicking down the road that we said we’d do
  * NOT remerging core with ansible/ansible this release cycle
* Community stuff
  * Define the process/ETA for reviewing PR’s from community
  * Publish better docs and how-tos for submitting code/features/fixes



















