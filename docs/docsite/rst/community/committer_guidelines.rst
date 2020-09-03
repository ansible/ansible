.. _community_committer_guidelines:

*********************
Committers Guidelines
*********************

These are the guidelines for people with commit privileges on the Ansible GitHub repository. Committers are essentially acting as members of the Ansible Core team, although not necessarily as employees of Ansible and Red Hat. Please read the guidelines before you commit.

These guidelines apply to everyone. At the same time, this ISN'T a process document. So just use good judgment. You've been given commit access because we trust your judgment.

That said, use the trust wisely.

If you abuse the trust and break components and builds, and so on, the trust level falls and you may be asked not to commit or you may lose your commit privileges.

Features, high-level design, and roadmap
========================================

As a core team member, you are an integral part of the team that develops the :ref:`roadmap <roadmaps>`. Please be engaged, and push for the features and fixes that you want to see. Also keep in mind that Red Hat, as a company, will commit to certain features, fixes, APIs, and so on, for various releases. Red Hat, the company, and the Ansible team must get these changes completed and released as scheduled. Obligations to users, the community, and customers must come first. Because of these commitments, a feature you want to develop yourself may not get into a release if it affects a lot of other parts within Ansible.

Any other new features and changes to high level design should go through the proposal process (TBD), to ensure the community and core team have had a chance to review the idea and approve it. The core team has sole responsibility for merging new features based on proposals.

Our workflow on GitHub
======================

As a committer, you may already know this, but our workflow forms a lot of our team policies. Please ensure you're aware of the following workflow steps:

* Fork the repository upon which you want to do some work to your own personal repository
* Work on the specific branch upon which you need to commit
* Create a Pull Request back to the Ansible repository and tag the people you would like to review; assign someone as the primary "owner" of your request
* Adjust code as necessary based on the Comments provided
* Ask someone on the Core Team to do a final review and merge

Addendum to workflow for committers:
------------------------------------

The Core Team is aware that this can be a difficult process at times. Sometimes, the team breaks the rules by making direct commits or merging their own PRs. This section is a set of guidelines. If you're changing a comma in a doc, or making a very minor change, you can use your best judgement. This is another trust thing. The process is critical for any major change, but for little things or getting something done quickly, use your best judgement and make sure people on the team are aware of your work.

Roles on Core
=============
* Core committers: Fine to do PRs for most things, but we should have a timebox. Hanging PRs may merge on the judgement of these devs.
* :ref:`Module maintainers <maintainers>`: Module maintainers own specific modules and have indirect commit access through the current module PR mechanisms.

General rules
=============
Individuals with direct commit access to ansible/ansible are entrusted with powers that allow them to do a broad variety of things--probably more than we can write down. Rather than rules, treat these as general *guidelines*, individuals with this power are expected to use their best judgement.

* Don't

  - Commit directly.
  - Merge your own PRs. Someone else should have a chance to review and approve the PR merge. If you are a Core Committer, you have a small amount of leeway here for very minor changes.
  - Forget about alternate environments. Consider the alternatives--yes, people have bad environments, but they are the ones who need us the most.
  - Drag your community team members down. Always discuss the technical merits, but you should never address the person's limitations (you can later go for beers and call them idiots, but not in IRC/GitHub/and so on).
  - Forget about the maintenance burden. Some things are really cool to have, but they might not be worth shoehorning in if the maintenance burden is too great.
  - Break playbooks. Always keep backwards compatibility in mind.
  - Forget to keep it simple. Complexity breeds all kinds of problems.

* Do

  - Squash, avoid merges whenever possible, use GitHub's squash commits or cherry pick if needed (bisect thanks you).
  - Be active. Committers who have no activity on the project (through merges, triage, commits, and so on) will have their permissions suspended.
  - Consider backwards compatibility (goes back to "don't break existing playbooks").
  - Write tests. PRs with tests are looked at with more priority than PRs without tests that should have them included. While not all changes require tests, be sure to add them for bug fixes or functionality changes.
  - Discuss with other committers, specially when you are unsure of something.
  - Document! If your PR is a new feature or a change to behavior, make sure you've updated all associated documentation or have notified the right people to do so. It also helps to add the version of ``ansible-base`` against which this documentation is compatible (to avoid confusion between stable and devel docs, for backwards compatibility, and so on).
  - Consider scope, sometimes a fix can be generalized
  - Keep it simple, then things are maintainable, debuggable and intelligible.

Committers are expected to continue to follow the same community and contribution guidelines followed by the rest of the Ansible community.


People
======

Individuals who've been asked to become a part of this group have generally been contributing in significant ways to the Ansible community for some time. Should they agree, they are requested to add their names and GitHub IDs to this file, in the section below, through a pull request. Doing so indicates that these individuals agree to act in the ways that their fellow committers trust that they will act.

+---------------------+----------------------+--------------------+----------------------+
| Name                | GitHub ID            | IRC Nick           | Other                |
+=====================+======================+====================+======================+
| James Cammarata     | jimi-c               | jimi               |                      |
+---------------------+----------------------+--------------------+----------------------+
| Brian Coca          | bcoca                | bcoca              |                      |
+---------------------+----------------------+--------------------+----------------------+
| Matt Davis          | nitzmahone           | nitzmahone         |                      |
+---------------------+----------------------+--------------------+----------------------+
| Toshio Kuratomi     | abadger              | abadger1999        |                      |
+---------------------+----------------------+--------------------+----------------------+
| Jason McKerr        | mckerrj              | newtMcKerr         |                      |
+---------------------+----------------------+--------------------+----------------------+
| Robyn Bergeron      | robynbergeron        | rbergeron          |                      |
+---------------------+----------------------+--------------------+----------------------+
| Greg DeKoenigsberg  | gregdek              | gregdek            |                      |
+---------------------+----------------------+--------------------+----------------------+
| Monty Taylor        | emonty               | mordred            |                      |
+---------------------+----------------------+--------------------+----------------------+
| Matt Martz          | sivel                | sivel              |                      |
+---------------------+----------------------+--------------------+----------------------+
| Nate Case           | qalthos              | Qalthos            |                      |
+---------------------+----------------------+--------------------+----------------------+
| James Tanner        | jctanner             | jtanner            |                      |
+---------------------+----------------------+--------------------+----------------------+
| Peter Sprygada      | privateip            | privateip          |                      |
+---------------------+----------------------+--------------------+----------------------+
| Abhijit Menon-Sen   | amenonsen            | crab               |                      |
+---------------------+----------------------+--------------------+----------------------+
| Michael Scherer     | mscherer             | misc               |                      |
+---------------------+----------------------+--------------------+----------------------+
| René Moser          | resmo                | resmo              |                      |
+---------------------+----------------------+--------------------+----------------------+
| David Shrewsbury    | Shrews               | Shrews             |                      |
+---------------------+----------------------+--------------------+----------------------+
| Sandra Wills        | docschick            | docschick          |                      |
+---------------------+----------------------+--------------------+----------------------+
| Graham Mainwaring   | ghjm                 |                    |                      |
+---------------------+----------------------+--------------------+----------------------+
| Chris Houseknecht   | chouseknecht         |                    |                      |
+---------------------+----------------------+--------------------+----------------------+
| Trond Hindenes      | trondhindenes        |                    |                      |
+---------------------+----------------------+--------------------+----------------------+
| Jon Hawkesworth     | jhawkesworth         | jhawkesworth       |                      |
+---------------------+----------------------+--------------------+----------------------+
| Will Thames         | willthames           | willthames         |                      |
+---------------------+----------------------+--------------------+----------------------+
| Adrian Likins       | alikins              | alikins            |                      |
+---------------------+----------------------+--------------------+----------------------+
| Dag Wieers          | dagwieers            | dagwieers          | dag@wieers.com       |
+---------------------+----------------------+--------------------+----------------------+
| Tim Rupp            | caphrim007           | caphrim007         |                      |
+---------------------+----------------------+--------------------+----------------------+
| Sloane Hertel       | s-hertel             | shertel            |                      |
+---------------------+----------------------+--------------------+----------------------+
| Sam Doran           | samdoran             | samdoran           |                      |
+---------------------+----------------------+--------------------+----------------------+
| Matt Clay           | mattclay             | mattclay           |                      |
+---------------------+----------------------+--------------------+----------------------+
| Martin Krizek       | mkrizek              | mkrizek            |                      |
+---------------------+----------------------+--------------------+----------------------+
| Ganesh Nalawade     | ganeshrn             | ganeshrn           |                      |
+---------------------+----------------------+--------------------+----------------------+
| Trishna Guha        | trishnaguha          | trishnag           |                      |
+---------------------+----------------------+--------------------+----------------------+
| Andrew Gaffney      | agaffney             | agaffney           |                      |
+---------------------+----------------------+--------------------+----------------------+
| Jordan Borean       | jborean93            | jborean93          |                      |
+---------------------+----------------------+--------------------+----------------------+
| Abhijeet Kasurde    | Akasurde             | akasurde           |                      |
+---------------------+----------------------+--------------------+----------------------+
| Adam Miller         | maxamillion          | maxamillion        |                      |
+---------------------+----------------------+--------------------+----------------------+
| Sviatoslav Sydorenko| webknjaz             | webknjaz           |                      |
+---------------------+----------------------+--------------------+----------------------+
| Alicia Cozine       | acozine              | acozine            |                      |
+---------------------+----------------------+--------------------+----------------------+
| Sandra McCann       | samccann             | samccann           |                      |
+---------------------+----------------------+--------------------+----------------------+
| Felix Fontein       | felixfontein         | felixfontein       | felix@fontein.de     |
+---------------------+----------------------+--------------------+----------------------+
