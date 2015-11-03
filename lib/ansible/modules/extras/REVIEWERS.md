Ansible Extras Reviewers
====================
The Ansible Extras Modules are written and maintained by the Ansible community, and are included in Extras through a community-driven approval process. 

Expectations
=======

1. New modules will be tested in good faith by users who care about them. 
2. New modules will adhere to the module guidelines, located here: http://docs.ansible.com/ansible/developing_modules.html#module-checklist
3. The submitter of the module is willing and able to maintain the module over time.

New Modules
=======

New modules are subject to review by anyone in the Ansible community. For inclusion of a new module into Ansible Extras, a pull request must receive at least one approval from a fellow community member on each of the following criteria:

* One "worksforme" approval from someone who has thoroughly tested the module, including all parameters and switches.
* One "passes_guidelines" approval from someone who has vetted the code according to the module guidelines.

Either of these approvals can be given, in a comment, by anybody (except the submitter).

Any module that has both of these, and no "needs_revision" votes (which can also be given by anybody) will be approved for inclusion.

The core team will continue to be the point of escalation for any issues that may arise (duplicate modules, disagreements over guidelines, etc.)

Existing Modules
=======

PRs made against existing modules in Extras are subject to review by the module author or current maintainer. 

Unmaintained Modules
=======

If modules in Extras go unmaintained, we will seek new maintainers, and if we don't find new
maintainers, we will ultimately deprecate them.

Subject Matter Experts
=======

Subject matter experts are groups of acknowledged community members who have expertise and experience in particular modules. Pull requests for existing or new modules are sometimes referred to these wider groups during triage, for expedience or escalation. 

Openstack: @emonty @shrews @dguerri @juliakreger @j2sol @rcarrillocruz

Windows: @trondhindenes @petemounce @elventear @smadam813 @jhawkesworth @angstwad @sivel @chrishoffman @cchurch

AWS: @jsmartin @scicoin-project @tombamford @garethr @jarv @jsdalton @silviud @adq @zbal @zeekin @willthames @lwade @carsongee @defionscode @tastychutney @bpennypacker @loia

Docker: @cove @joshuaconner @softzilla @smashwilson

Red Hat Network: @barnabycourt @vritant @flossware

Zabbix: @cove @harrisongu @abulimov

PR Process
=======

A full view of the pull request process for Extras can be seen here: 
![here](http://gregdek.org/extras_PR_process_2015_09.png)
