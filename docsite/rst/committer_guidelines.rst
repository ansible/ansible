Committers Guidelines (for people with commit rights to Ansible on GitHub)
``````````````````````````````````````````````````````````````````````````

These are the guidelines for people with commit access to Ansible. Committers are essentially acting as members of the Ansible Core team, although not necessarily as an employee of Ansible and Red Hat. Please read the guidelines before you commit.

These guidelines apply to everyone. At the same time, this ISN’T a process document. So just use good judgement. You’ve been given commit access because we trust your judgement.

That said, use the trust wisely. 

If you abuse the trust and break components and builds, etc., the trust level falls and you may be asked not to commit or you may lose access to do so.

Features, High Level Design, and Roadmap
========================================

As a core team member, you are an integral part of the team that develops the roadmap. Please be engaged, and push for the features and fixes that you want to see. Also keep in mind that Red Hat, as a company, will commit to certain features, fixes, APIs, etc. for various releases. Red Hat, the company, and the Ansible team must get these committed features (etc.) completed and released as scheduled. Obligations to users, the community, and customers must come first. Because of thse commitments, a feature you want to develop yourself many not get into a release if it impacts a lot of other parts within Ansible.

Any other new features and changes to high level design should go through the proposal process (TBD), to ensure the community and core team have had a chance to review the idea and approve it. The core team has sole responsibility for merging new features based on proposals.

Our Workflow on GitHub
======================

As a committer, you may already know this, but our workflow forms a lot of our team policies. Please ensure you’re aware of the following workflow steps:

* Fork the repository upon which you want to do some work to your own personal repository
* Work on the specific branch upon which you need to commit
* Create a Pull Request back to the Ansible repository and tag the people you would like to review; assign someone as the primary “owner” of your request
* Adjust code as necessary based on the Comments provided
* Ask someone on the Core Team to do a final review and merge

Addendum to workflow for Committers:
------------------------------------

The Core Team is aware that this can be a difficult process at times. Sometimes, the team breaks the rules: Direct commits, merging their own PRs. This section is a set of guidelines. If you’re changing a comma in a doc, or making a very minor change, you can use your best judgement. This is another trust thing. The process is critical for any major change, but for little things or getting something done quickly, use your best judgement and make sure people on the team are aware of your work.

Roles on Core
=============
* Core Committers: Fine to do PRs for most things, but we should have a timebox. Hanging PRs may merge on the judgement of these devs.
* Module Owners: Module Owners own specific modules and have indirect commit access via the current module PR mechanisms.

General Rules
=============
Individuals with direct commit access to ansible/ansible (+core, + extras) are entrusted with powers that allow them to do a broad variety of things--probably more than we can write down. Rather than rules, treat these as general *guidelines*, individuals with this power are expected to use their best judgement. 

* Don’t commit directly.
* Don't omit tests. PRs with tests are looked at with more priority than PRs without tests that should have them included. While not all changes require tests, be sure to add them for bug fixes or functionality changes.
* Don't forget the docs! If your PR is a new feature or a change to behavior, make sure you've updated all associated documentation or have notified the right people to do so. It also helps to add the version of Core against which this documentation is compatible (to avoid confusion with stable versus devel docs, for backwards compatibility, etc.).
* Don't merge your own PRs. Someone else should have a chance to review and approve the PR merge. If you are a Core Committer, you have a small amount of leeway here for very minor changes.
* Consider backwards compatibility (don’t break existing playbooks).
* Don't forget about alternate environments. Consider the alternatives--yes, people have bad environments, but they are the ones who need us the most.
* Don't drag your community team members down. Always discuss the technical merits, but you should never address the person’s limitations (you can later go for beers and call them idiots, but not in IRC/Github/etc.).
* Don't forget about the maintenance burden. Some things are really cool to have, but they might not be worth shoehorning in if the maintenance burden is too great.
* Don't break playbooks. Always keep backwards compatibility in mind.
* Don't forget to keep it simple. Complexity breeds all kinds of problems.
* Don't forget to be active. Committers who have no activity on the project (through merges, triage, commits, etc.) will have their permissions suspended.

Committers are expected to continue to follow the same community and contribution guidelines followed by the rest of the Ansible community. 


People
======
Individuals who've been asked to become a part of this group have generally been contributing in significant ways to the Ansible community for some time. Should they agree, they are requested to add their names and GitHub IDs to this file, in the section below, via a pull request. Doing so indicates that these individuals agree to act in the ways that their fellow committers trust that they will act.

* James Cammarata (RedHat/Ansible)
* Brian Coca (RedHat/Ansible)
* Matt Davis (RedHat/Ansible)
* Toshio Kuratomi (RedHat/Ansible)
* Jason McKerr (RedHat/Ansible)
* Robyn Bergeron (RedHat/Ansible)
* Greg DeKoenigsberg (RedHat/Ansible
* Monty Taylor
* Matt Martz 

