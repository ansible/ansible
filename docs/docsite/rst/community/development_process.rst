.. _community_development_process:

The Ansible Development Process
===============================

.. contents:: Topics

This section discusses how the Ansible development and triage process works.

Road Maps
=========

The Ansible Core team provides a road map for each upcoming release. These road maps can be found :ref:`here <roadmaps>`.

.. Roadmaps are User-oriented.  We should also list the Roadmap Projects and the Blocker Bug
   Projects here

.. How the actual release schedule, slipping, etc relates to (release_and_maintenance.rst) probably
   also belongs here somewhere

Pull Requests
=============

Ansible accepts code via **pull requests** ("PRs" for short). GitHub provides a great overview of `how the pull request process works <https://help.github.com/articles/about-pull-requests/>`_ in general.

Because Ansible receives many pull requests, we use an automated process to help us through the process of reviewing and merging pull requests. That process is managed by **Ansibullbot**.

Backport Pull Request Process
-----------------------------

After the pull request submitted to Ansible for the ``devel`` branch is
accepted and merged, the following instructions will help you create a
pull request to backport the change to a previous stable branch.

.. note::

    These instructions assume that ``stable-2.5`` is the targeted release
    branch for the backport.

.. note::

    These instructions assume that ``https://github.com/ansible/ansible.git``
    is configured as a ``git remote`` named ``upstream``. If you do not use
    a ``git remote`` named ``upstream``, adjust the instructions accordingly.

.. note::

   These instructions assume that ``https://github.com/<yourgithubaccount>/ansible.git``
   is configured as a ``git remote`` named ``origin``. If you do not use
   a ``git remote`` named ``origin``, adjust the instructions accordingly.

#. Prepare your devel, stable, and feature branches:

   ::

       git fetch upstream
       git checkout -b backport/2.5/[PR_NUMBER_FROM_DEVEL] upstream/stable-2.5

#. Cherry pick the relevant commit SHA from the devel branch into your feature
   branch, handling merge conflicts as necessary:

   ::

       git cherry-pick -x [SHA_FROM_DEVEL]

#. Add a changelog entry for the change, and commit it.

#. Push your feature branch to your fork on GitHub:

   ::

       git push origin backport/2.5/[PR_NUMBER_FROM_DEVEL]

#. Submit the pull request for ``backport/2.5/[PR_NUMBER_FROM_DEVEL]``
   against the ``stable-2.5`` branch

.. note::

    The choice to use ``backport/2.5/[PR_NUMBER_FROM_DEVEL]`` as the
    name for the feature branch is somewhat arbitrary, but conveys meaning
    about the purpose of that branch. It is not required to use this format,
    but it can be helpful, especially when making multiple backport PRs for
    multiple stable branches.

.. note::

    If you prefer, you can use CPython's cherry-picker tool to backport commits
    from devel to stable branches in Ansible. Take a look at the `cherry-picker
    documentation <https://pypi.org/p/cherry-picker#cherry-picking>`_ for
    details on installing, configuring, and using it.


Ansibullbot
===========

Overview
--------

`Ansibullbot`_ serves many functions:

- Responds quickly to PR submitters to thank them for submitting their PR
- Identifies the community maintainer responsible for reviewing PRs for any files affected
- Tracks the current status of PRs
- Pings responsible parties to remind them of any PR actions for which they may be responsible
- Provides maintainers with the ability to move PRs through the workflow
- Identifies PRs abandoned by their submitters so that we can close them
- Identifies modules abandoned by their maintainers so that we can find new maintainers

Community Maintainers
---------------------

Each module has at least one assigned maintainer, listed in a `maintainer's file`_:

.. _Ansibullbot: https://github.com/ansible/ansibullbot/blob/master/ISSUE_HELP.md
.. _maintainer's file: https://github.com/ansible/ansible/blob/devel/.github/BOTMETA.yml

Some modules have no community maintainers assigned. In this case, the maintainer is listed as ``$team_ansible``. Ultimately, it's our goal to have at least one community maintainer for every module.

The maintainer's job is to review PRs and decide whether that PR should be merged (``shipit``) or revised (``needs_revision``).

The ultimate goal of any pull request is to reach **shipit** status, where the Core team then decides whether the PR is ready to be merged. Not every PR that reaches the **shipit** label is actually ready to be merged, but the better our reviewers are, and the better our guidelines are, the more likely it will be that a PR that reaches **shipit** will be mergeable.



Workflow
--------

Ansibullbot runs continuously. You can generally expect to see changes to your issue or pull request within thirty minutes. Ansibullbot examines every open pull request in the repositories, and enforces state roughly according to the following workflow:

-  If a pull request has no workflow labels, it's considered **new**. Files in the pull request are identified, and the maintainers of those files are pinged by the bot, along with instructions on how to review the pull request. (Note: sometimes we strip labels from a pull request to "reboot" this process.)
-  If the module maintainer is not ``$team_ansible``, the pull request then goes into the **community_review** state.
-  If the module maintainer is ``$team_ansible``, the pull request then goes into the **core_review** state (and probably sits for a while).
-  If the pull request is in **community_review** and has received comments from the maintainer:

   -  If the maintainer says ``shipit``, the pull request is labeled **shipit**, whereupon the Core team assesses it for final merge.
   -  If the maintainer says ``needs_info``, the pull request is labeled **needs_info** and the submitter is asked for more info.
   -  If the maintainer says **needs_revision**, the pull request is labeled **needs_revision** and the submitter is asked to fix some things.

-  If the submitter says ``ready_for_review``, the pull request is put back into **community_review** or **core_review** and the maintainer is notified that the pull request is ready to be reviewed again.
-  If the pull request is labeled **needs_revision** or **needs_info** and the submitter has not responded lately:

   -  The submitter is first politely pinged after two weeks, pinged again after two more weeks and labeled **pending action**, and the issue or pull request will be closed two weeks after that.
   -  If the submitter responds at all, the clock is reset.
-  If the pull request is labeled **community_review** and the reviewer has not responded lately:

   -  The reviewer is first politely pinged after two weeks, pinged again after two more weeks and labeled **pending_action**, and then may be reassigned to ``$team_ansible`` or labeled **core_review**, or often the submitter of the pull request is asked to step up as a maintainer.
-  If Shippable tests fail, or if the code is not able to be merged, the pull request is automatically put into **needs_revision** along with a message to the submitter explaining why.


There are corner cases and frequent refinements, but this is the workflow in general.

PR Labels
---------

There are two types of PR Labels generally: *workflow labels* and *information labels*.

Workflow Labels
~~~~~~~~~~~~~~~

-  **community_review**: Pull requests for modules that are currently awaiting review by their maintainers in the Ansible community.
-  **core_review**: Pull requests for modules that are currently awaiting review by their maintainers on the Ansible Core team.
-  **needs_info**: Waiting on info from the submitter.
-  **needs_rebase**: Waiting on the submitter to rebase.
-  **needs_revision**: Waiting on the submitter to make changes.
-  **shipit**: Waiting for final review by the core team for potential merge.

Informational Labels
~~~~~~~~~~~~~~~~~~~~

-  **backport**: this is applied automatically if the PR is requested against any branch that is not devel. The bot immediately assigns the labels backport and ``core_review``.
-  **bugfix_pull_request**: applied by the bot based on the templatized description of the PR.
-  **cloud**: applied by the bot based on the paths of the modified files.
-  **docs_pull_request**: applied by the bot based on the templatized description of the PR.
-  **easyfix**: applied manually, inconsistently used but sometimes useful.
-  **feature_pull_request**: applied by the bot based on the templatized description of the PR.
-  **networking**: applied by the bot based on the paths of the modified files.
-  **owner_pr**: largely deprecated. Formerly workflow, now informational. Originally, PRs submitted by the maintainer would automatically go to **shipit** based on this label. If the submitter is also a maintainer, we notify the other maintainers and still require one of the maintainers (including the submitter) to give a **shipit**.
-  **pending_action**: applied by the bot to PRs that are not moving. Reviewed every couple of weeks by the community team, who tries to figure out the appropriate action (closure, asking for new maintainers, etc).


Special Labels
~~~~~~~~~~~~~~

-  **new_plugin**: this is for new modules or plugins that are not yet in Ansible.

   **Note:** `new_plugin` kicks off a completely separate process, and frankly it doesn't work very well at present. We're working our best to improve this process.
