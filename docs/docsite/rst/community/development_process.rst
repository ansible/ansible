.. _community_development_process:

*****************************
The Ansible Development Cycle
*****************************

Ansible developers (including community contributors) add new features, fix bugs, and update code in many different repositories. The `ansible/ansible repository <https://github.com/ansible/ansible>`_ contains the code for basic features and functions, such as copying module code to managed nodes. This code is also known as ``ansible-base``. Other repositories contain plugins and modules that enable Ansible to execute specific tasks, like adding a user to a particular database or configuring a particular network device. These repositories contain the source code for collections.

Development on ``ansible-base`` occurs on two levels. At the macro level, the ``ansible-base`` developers and maintainers plan releases and track progress with roadmaps and projects. At the micro level, each PR has its own lifecycle.

Development on collections also occurs at the macro and micro levels. Each collection has its own macro development cycle. For more information on the collections development cycle, see :ref:`contributing_maintained_collections`. The micro-level lifecycle of a PR is similar in collections and in ``ansible-base``.

.. contents::
   :local:

Macro development: ``ansible-base`` roadmaps, releases, and projects
=====================================================================

If you want to follow the conversation about what features will be added to ``ansible-base`` for upcoming releases and what bugs are being fixed, you can watch these resources:

* the :ref:`roadmaps`
* the :ref:`Ansible Release Schedule <release_and_maintenance>`
* various GitHub `projects <https://github.com/ansible/ansible/projects>`_ - for example:

   * the `2.10 release project <https://github.com/ansible/ansible/projects/39>`_
   * the `network bugs project <https://github.com/ansible/ansible/projects/20>`_
   * the `core documentation project <https://github.com/ansible/ansible/projects/27>`_

.. _community_pull_requests:

Micro development: the lifecycle of a PR
========================================

If you want to contribute a feature or fix a bug in ``ansible-base`` or in a collection, you must open a **pull request** ("PR" for short). GitHub provides a great overview of `how the pull request process works <https://help.github.com/articles/about-pull-requests/>`_ in general. The ultimate goal of any pull request is to get merged and become part of a collection or ``ansible-base``.
Here's an overview of the PR lifecycle:

* Contributor opens a PR
* Ansibot reviews the PR
* Ansibot assigns labels
* Ansibot pings maintainers
* Shippable runs the test suite
* Developers, maintainers, community review the PR
* Contributor addresses any feedback from reviewers
* Developers, maintainers, community re-review
* PR merged or closed

Automated PR review: ansibullbot
--------------------------------

Because Ansible receives many pull requests, and because we love automating things, we have automated several steps of the process of reviewing and merging pull requests with a tool called Ansibullbot, or Ansibot for short.

`Ansibullbot <https://github.com/ansible/ansibullbot/blob/master/ISSUE_HELP.md>`_ serves many functions:

- Responds quickly to PR submitters to thank them for submitting their PR
- Identifies the community maintainer responsible for reviewing PRs for any files affected
- Tracks the current status of PRs
- Pings responsible parties to remind them of any PR actions for which they may be responsible
- Provides maintainers with the ability to move PRs through the workflow
- Identifies PRs abandoned by their submitters so that we can close them
- Identifies modules abandoned by their maintainers so that we can find new maintainers

Ansibot workflow
^^^^^^^^^^^^^^^^

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

PR labels
^^^^^^^^^

There are two types of PR Labels generally: **workflow** labels and **information** labels.

Workflow labels
"""""""""""""""

-  **community_review**: Pull requests for modules that are currently awaiting review by their maintainers in the Ansible community.
-  **core_review**: Pull requests for modules that are currently awaiting review by their maintainers on the Ansible Core team.
-  **needs_info**: Waiting on info from the submitter.
-  **needs_rebase**: Waiting on the submitter to rebase.
-  **needs_revision**: Waiting on the submitter to make changes.
-  **shipit**: Waiting for final review by the core team for potential merge.

Information labels
""""""""""""""""""

-  **backport**: this is applied automatically if the PR is requested against any branch that is not devel. The bot immediately assigns the labels backport and ``core_review``.
-  **bugfix_pull_request**: applied by the bot based on the templatized description of the PR.
-  **cloud**: applied by the bot based on the paths of the modified files.
-  **docs_pull_request**: applied by the bot based on the templatized description of the PR.
-  **easyfix**: applied manually, inconsistently used but sometimes useful.
-  **feature_pull_request**: applied by the bot based on the templatized description of the PR.
-  **networking**: applied by the bot based on the paths of the modified files.
-  **owner_pr**: largely deprecated. Formerly workflow, now informational. Originally, PRs submitted by the maintainer would automatically go to **shipit** based on this label. If the submitter is also a maintainer, we notify the other maintainers and still require one of the maintainers (including the submitter) to give a **shipit**.
-  **pending_action**: applied by the bot to PRs that are not moving. Reviewed every couple of weeks by the community team, who tries to figure out the appropriate action (closure, asking for new maintainers, and so on).


Special Labels
""""""""""""""

-  **new_plugin**: this is for new modules or plugins that are not yet in Ansible.

**Note:** `new_plugin` kicks off a completely separate process, and frankly it doesn't work very well at present. We're working our best to improve this process.

Human PR review
---------------

After Ansibot reviews the PR and applies labels, the PR is ready for human review. The most likely reviewers for any PR are the maintainers for the module that PR modifies.

Each module has at least one assigned :ref:`maintainer <maintainers>`, listed in the `BOTMETA.yml <https://github.com/ansible/ansible/blob/devel/.github/BOTMETA.yml>`_ file.

The maintainer's job is to review PRs that affect that module and decide whether they should be merged (``shipit``) or revised (``needs_revision``). We'd like to have at least one community maintainer for every module. If a module has no community maintainers assigned, the maintainer is listed as ``$team_ansible``.

Once a human applies the ``shipit`` label, the :ref:`committers <community_committer_guidelines>` decide whether the PR is ready to be merged. Not every PR that gets the ``shipit`` label is actually ready to be merged, but the better our reviewers are, and the better our guidelines are, the more likely it will be that a PR that reaches **shipit** will be mergeable.


Making your PR merge-worthy
===========================

We do not merge every PR. Here are some tips for making your PR useful, attractive, and merge-worthy.

.. _community_changelogs:

Changelogs
----------

Changelogs help users and developers keep up with changes to Ansible. Ansible builds a changelog for each release from fragments. You **must** add a changelog fragment to any PR that changes functionality or fixes a bug in ansible-base. You do not have to add a changelog fragment for PRs that add new modules and plugins, because our tooling does that for you automatically.

We build short summary changelogs for minor releases as well as for major releases. If you backport a bugfix, include a changelog fragment with the backport PR.

.. _changelogs_how_to:

Creating a changelog fragment
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

A basic changelog fragment is a ``.yaml`` file placed in the ``changelogs/fragments/`` directory.  Each file contains a yaml dict with keys like ``bugfixes`` or ``major_changes`` followed by a list of changelog entries of bugfixes or features.  Each changelog entry is rst embedded inside of the yaml file which means that certain constructs would need to be escaped so they can be interpreted by rst and not by yaml (or escaped for both yaml and rst if you prefer).  Each PR **must** use a new fragment file rather than adding to an existing one, so we can trace the change back to the PR that introduced it.

To create a changelog entry, create a new file with a unique name in the ``changelogs/fragments/`` directory of the corresponding repository. The file name should include the PR number and a description of the change. It must end with the file extension ``.yaml``. For example: ``40696-user-backup-shadow-file.yaml``

A single changelog fragment may contain multiple sections but most will only contain one section. The toplevel keys (bugfixes, major_changes, and so on) are defined in the `config file <https://github.com/ansible/ansible/blob/devel/changelogs/config.yaml>`_ for our `release note tool <https://github.com/ansible-community/antsibull-changelog/blob/main/docs/changelogs.rst>`_. Here are the valid sections and a description of each:

**breaking_changes**
  Changes that break existing playbooks or roles. This includes any change to existing behavior that forces users to update tasks. Displayed in both the changelogs and the :ref:`Porting Guides <porting_guides>`.

**major_changes**
  Major changes to Ansible itself. Generally does not include module or plugin changes. Displayed in both the changelogs and the :ref:`Porting Guides <porting_guides>`.

**minor_changes**
  Minor changes to Ansible, modules, or plugins. This includes new features, new parameters added to modules, or behavior changes to existing parameters.

**deprecated_features**
  Features that have been deprecated and are scheduled for removal in a future release. Displayed in both the changelogs and the :ref:`Porting Guides <porting_guides>`.

**removed_features**
  Features that were previously deprecated and are now removed. Displayed in both the changelogs and the :ref:`Porting Guides <porting_guides>`.

**security_fixes**
  Fixes that address CVEs or resolve security concerns. Include links to CVE information.

**bugfixes**
  Fixes that resolve issues.

**known_issues**
  Known issues that are currently not fixed or will not be fixed.

Each changelog entry must contain a link to its issue between parentheses at the end. If there is no corresponding issue, the entry must contain a link to the PR itself.

Most changelog entries will be ``bugfixes`` or ``minor_changes``. When writing a changelog entry that pertains to a particular module, start the entry with ``- [module name] -`` and the following sentence with a lowercase letter.

Here are some examples:

.. code-block:: yaml

  bugfixes:
    - apt_repository - fix crash caused by ``cache.update()`` raising an ``IOError``
      due to a timeout in ``apt update`` (https://github.com/ansible/ansible/issues/51995).

.. code-block:: yaml

  minor_changes:
    - lineinfile - add warning when using an empty regexp (https://github.com/ansible/ansible/issues/29443).

.. code-block:: yaml

  bugfixes:
    - copy - the module was attempting to change the mode of files for
      remote_src=True even if mode was not set as a parameter.  This failed on
      filesystems which do not have permission bits (https://github.com/ansible/ansible/issues/29444).

You can find more example changelog fragments in the `changelog directory <https://github.com/ansible/ansible/tree/stable-2.10/changelogs/fragments>`_ for the 2.10 release.

After you have written the changelog fragment for your PR, commit the file and include it with the pull request.

.. _backport_process:

Backporting merged PRs in ``ansible-base``
===========================================

All ``ansible-base`` PRs must be merged to the ``devel`` branch first. After a pull request has been accepted and merged to the ``devel`` branch, the following instructions will help you create a pull request to backport the change to a previous stable branch.

We do **not** backport features.

.. note::

   These instructions assume that:

    * ``stable-2.10`` is the targeted release branch for the backport
    * ``https://github.com/ansible/ansible.git`` is configured as a
      ``git remote`` named ``upstream``. If you do not use
      a ``git remote`` named ``upstream``, adjust the instructions accordingly.
    * ``https://github.com/<yourgithubaccount>/ansible.git``
      is configured as a ``git remote`` named ``origin``. If you do not use
      a ``git remote`` named ``origin``, adjust the instructions accordingly.

#. Prepare your devel, stable, and feature branches:

   ::

       git fetch upstream
       git checkout -b backport/2.10/[PR_NUMBER_FROM_DEVEL] upstream/stable-2.10

#. Cherry pick the relevant commit SHA from the devel branch into your feature
   branch, handling merge conflicts as necessary:

   ::

       git cherry-pick -x [SHA_FROM_DEVEL]

#. Add a :ref:`changelog fragment <changelogs_how_to>` for the change, and commit it.

#. Push your feature branch to your fork on GitHub:

   ::

       git push origin backport/2.10/[PR_NUMBER_FROM_DEVEL]

#. Submit the pull request for ``backport/2.10/[PR_NUMBER_FROM_DEVEL]``
   against the ``stable-2.10`` branch

#. The Release Manager will decide whether to merge the backport PR before
   the next minor release. There isn't any need to follow up. Just ensure that the automated
   tests (CI) are green.

.. note::

    The choice to use ``backport/2.10/[PR_NUMBER_FROM_DEVEL]`` as the
    name for the feature branch is somewhat arbitrary, but conveys meaning
    about the purpose of that branch. It is not required to use this format,
    but it can be helpful, especially when making multiple backport PRs for
    multiple stable branches.

.. note::

    If you prefer, you can use CPython's cherry-picker tool
    (``pip install --user 'cherry-picker >= 1.3.2'``) to backport commits
    from devel to stable branches in Ansible. Take a look at the `cherry-picker
    documentation <https://pypi.org/p/cherry-picker#cherry-picking>`_ for
    details on installing, configuring, and using it.
