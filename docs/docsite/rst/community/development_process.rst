The Ansible Development Process
===============================

This section discusses how the Ansible development and triage process works.

The Triage Bot
==============


Overview
--------

The `Ansibull PR Triage Bot`_ serves many functions: \* Responds quickly
to PR submitters to thank them for submitting their PR; \* Identifies
the community maintainer responsible for reviewing PRs for any files
affected; \* Tracks the current status of PRs; \* Pings responsible
parties to remind them of any PR actions that they may be responsible
for; \* Provides maintainers with the ability to move PRs through our
workflow; \* Identifies PRs abandoned by their submitters so that we can
close them; \* Identifies modules abandoned by their maintainers so that
we can find new maintainers.

Community Maintainers
---------------------

Each module in Core and Extras has at least one assigned maintainer,
listed in two maintainers files: one for `Core`_ and one for `Extras`_.

Some modules have no community maintainers assigned. In this case, the
maintainer is listed as “ansible”. Ultimately, it’s our goal to have at
least one community maintainer for every module.

The maintainer’s job is to review PRs and decide whether that PR should
be merged (“shipit!”) or revised (“needs\_revision”).

The ultimate goal of any Pull Request is to reach “shipit” status, where
the Core team then decides whether the PR is ready to be merged. Not
every PR that reaches the “shipit” label is actually ready to be merged,
but the better our reviewers are, and the better our guidelines are, the
more likely it will be that a PR that reaches “shipit” will be
mergeable.

.. _Ansibull PR Triage Bot: https://github.com/ansible/ansibullbot/blob/master/triage.py
.. _Core: https://github.com/ansible/ansibullbot/blob/master/MAINTAINERS-CORE.txt
.. _Extras: https://github.com/ansible/ansibullbot/blob/master/MAINTAINERS-CORE.txt

Some modules have no community maintainers assigned. In this case, the
maintainer is listed as “ansible”. Ultimately, it’s our goal to have at
least one community maintainer for every module.

The maintainer’s job is to review PRs and decide whether that PR should
be merged (“shipit!”) or revised (“needs\_revision”).

The ultimate goal of any Pull Request is to reach “shipit” status, where
the Core team then decides whether the PR is ready to be merged. Not
every PR that reaches the “shipit” label is actually ready to be merged,
but the better our reviewers are, and the better our guidelines are, the
more likely it will be that a PR that reaches “shipit” will be
mergeable.

Workflow
--------

The triage bot runs every six hours and examines every open PR in both
core and extras repositories, and enforces state roughly according to
the following workflow:

-  If a PR has no workflow labels, it’s considered “new”. Files in the
   PR are identified, and the maintainers of those files are pinged by
   the bot, along with instructions on how to review the PR. (Note:
   sometimes we strip labels from a PR to “reboot” this process.)
-  If the module maintainer is not “ansible”, the PR then goes into the
   “community\_review” state.
-  If the module maintainer is “ansible”, the PR then goes into the
   “core\_review” state (and probably sits for a while).
-  If the PR is in “community\_review” and has received comments from
   the maintainer:
-  If the maintainer says “shipit”, the PR is labeled “shipit”,
   whereupon the Core team assesses it for final merge.
-  If the maintainer says “needs\_info”, the PR is labeled “needs\_info”
   and the submitter is asked for more info.
-  If the maintainer says “needs\_revision”, the PR is labeled
   “needs\_revision” and the submitter is asked to fix some things.
-  If the PR is in “needs\_revision/needs\_info” and has received
   comments from the submitter:
-  If the submitter says “ready\_for\_review”, the PR is put back into
   community\_review/core\_review and the maintainer is notified that
   the PR is ready to be reviewed again.
-  If the PR is in “needs\_revision/needs\_info” and the submitter has
   not responded lately:
-  The submitter is first politely pinged after two weeks, pinged again
   after two more weeks and labeled “pending action”, and then may be
   closed two weeks after that.
-  If the submitter responds at all, the clock is reset.
-  If the PR is in “community\_review” and the reviewer has not
   responded lately:
-  The reviewer is first politely pinged after two weeks, pinged again
   after two more weeks and labeled “pending\_action”, and then may be
   reassigned to “ansible” / core\_review, or often the submitter of the
   PR is asked to step up as a maintainer.
-  If Travis fails, or if the code is not mergable, the PR is
   automatically put into “needs\_revision” along with a message to the
   submitter explaining why.


There are corner cases and frequent refinements, but this is the workflow in general. 

PR Labels
---------

There are two types of PR Labels generally: *workflow labels* and
*information labels*.

Workflow Labels
~~~~~~~~~~~~~~~

-  **community\_review**: Pull requests for modules that are currently
   awaiting review by their maintainers in the Ansible community.
-  **core\_review**: Pull requests for modules that are currently
   awaiting review by their maintainers on the Ansible Core team.
-  **needs\_info**: Waiting on info from the submitter.
-  **needs\_rebase**: Waiting on the submitter to rebase. (Note: no
   longer used by the bot.)
-  **needs\_revision**: Waiting on the submitter to make changes.
-  **shipit**: Waiting for final review by the core team for potential
   merge.

Informational Labels
~~~~~~~~~~~~~~~~~~~~

-  **backport**: this is applied automatically if the PR is requested
   against any branch that is not devel. The bot immediately assigns the
   labels “backport” and “core\_review”.
-  **bugfix\_pull\_request**: applied by the bot based on the
   templatized description of the PR.
-  **cloud**: applied by the bot based on the paths of the modified
   files.
-  **docs\_pull\_request**: applied by the bot based on the templatized
   description of the PR.
-  **easyfix**: applied manually, inconsistently used but sometimes
   useful.
-  **feature\_pull\_request**: applied by the bot based on the
   templatized description of the PR.
-  **networking**: applied by the bot based on the paths of the modified
   files.
-  **owner\_pr**: largely deprecated. Formerly workflow, now
   informational. Originally, PRs submitted by the maintainer would
   automatically go to “shipit” based on this label; now, if the
   submitter is also a maintainer, we notify the other maintainers and
   still require one of the maintainers (including the submitter) to
   give a “shipit”.
-  **P1 - P5**: deprecated for modules because they were wildly
   inconsistent and not useful. The bot now strips these.
-  **pending\_action**: applied by the bot to PRs that are not moving.
   Reviewed every couple of weeks by the community team, who tries to
   figure out the appropriate action (closure, asking for new
   maintainers, etc).


Special Labels
~~~~~~~~~~~~~~

-  **new\_plugin**: this is for new modules or plugins that are not yet
   in Ansible. **Note: this kicks off a completely separate process, and
   frankly it doesn’t work very well at present. We’re working our best
   to improve this process.**