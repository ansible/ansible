Committers Guidelines (for people with commit rights to Ansible on GitHub)
``````````````````````````````````````````````````````````````````````````

These are the guidelines for people with commit access to Ansible. Committers are essentially acting as members of the Ansible Core team, although not necessarily as an employee of Ansible and Red Hat. Please read the guidelines before you commit.

These guidelines apply to everyone. At the same time, this ISN’T a process document. So just use good judgement. You’ve been given commit access because we trust your judgement.

That said, use the trust wisely. 

If you abuse the trust and break components and builds, or waste a lot of time asking people to review incomplete or untested pull requests, the trust level falls and you may be asked not to commit or you may lose access to do so.

Features, High Level Design, and Roadmap
========================================

As a core team member you will be part of the team that actually develops the roadmap! So be engaged and push for what you want. However, Red Hat as a company will commit to certain features, fixes, APIs, etc. for various releases. The company and the Ansible team still has to get those done and out the door. Obligations to users, the community, and customers come first. Because of that, a feature you may want to develop yourself may not get into a release if it impacts a lot of other parts of Ansible.  

Any other new features and changes to high level design should go through the proposal process (TBD), to ensure the community and core team have had a chance to review the idea and approve it. The core team will have sole responsibility for merging new features based on proposals.

Our Workflow on GitHub
======================

As a committer, you may already know this, but our workflow forms a lot of our team policies. Please ensure you’re aware of the following workflow steps:

* Fork the repository upon which you want to do some work
* Work on the specific branch upon which you need to commit
* Create a Pull Request and tag the people you would like to review; assign someone as the primary “owner” of your request
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
Individuals with direct commit access to ansible/ansible (+core, + extras) are entrusted with powers that allow them to do a broad variety of things--probably more than we can write down. Rather than a list of what you *can* do, this is a list of what you *should not* do and, in lieu of anything else, individuals with this power are expected to use their best judgement. 

* Don’t commit directly.
* PRs that have tests will be looked at with more priority than PRs without tests. Of course not all changes require tests, but for bug fixes or functionality changes, please add tests.
* Documentation. If your PR is new feature or a change to behavior, make sure you’ve updated associated documentation or notified the right people to do so. It also helps to add the version of Core against which this documentation is compatible (to avoid confusion with stable versus devel docs, for backwards compatibility, etc.).
* Someone else should merge your pull requests. If you are a Core Committer you have leeway here for minor changes.
* After a merge clean up dead forks/branches. Don’t leave a mess hanging around.
* Consider backwards compatibility (don’t break existing playbooks).
* Consider alternate environments (yes, people have bad environments, but they are the ones that need us the most).
* Always discuss the technical merits, never address the person’s limitations (you can later go for beers and call them idiots, but not in IRC/Github/etc).
* Consider the maintenance burden, some things are cool to have, but might not be worth shoehorning in.
* Complexity breeds all kinds of problems, so keep it simple.
* Lastly, comitters that have no activity on the project (merges, triage, commits, etc) will have permissions suspended.

Committers are expected to continue to follow the same community and contribution guidelines followed by the rest of the Ansible community. 


People
======
Individuals who have been asked to become part of this group have generally been contributing in significant ways to the Ansible community for some time. Should they agree, they are requested to add their names & github IDs to this file below via pull request, indicating that they agree to act in the ways that their fellow committers trust that they will act. 

* James Cammarata (RedHat/Ansible)
* Brian Coca (RedHat/Ansible)
* Matt Davis (RedHat/Ansible)
* Toshio Kuratomi (RedHat/Ansible)
* Jason McKerr (RedHat/Ansible)
* Robyn Bergeron (RedHat/Ansible)
* Greg DeKoenigsberg (RedHat/Ansible
* Monty Taylor
* Matt Martz 

