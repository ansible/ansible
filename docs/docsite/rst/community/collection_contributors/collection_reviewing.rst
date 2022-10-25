.. _review_checklist:

Review checklist for collection PRs
====================================

Use this section as a checklist reminder of items to review when you review a collection PR.

Reviewing bug reports
----------------------

When users report bugs, verify the behavior reported. Remember always to be kind with your feedback.

*  Did the user make a mistake in the code they put in the Steps to Reproduce issue section? We often see user errors reported as bugs.
*  Did the user assume an unexpected behavior? Ensure that the related documentation is clear. If not, the issue is useful to help us improve documentation.
*  Is there a minimal reproducer? If not, ask the reporter to reduce the complexity to help pinpoint the issue.
*  Is the issue a consequence of a wrongly-configured environment?
*  If it seems to be a real bug, does the behaviour still exist in the most recent release or the development branch?
*  Reproduce the bug, or if you do not have a suitable infrastructure, ask other contributors to reproduce the bug.


Reviewing suggested changes
---------------------------

When reviewing PRs, verify the suggested changes first. Verify that suggested changes do not:

*  Unnecessarily break backward compatibility.
*  Bring more harm than value.
*  Introduce non-idempotent solutions.
*  Duplicate already existing features (inside or outside the collection).
*  Violate the :ref:`Ansible development conventions <module_conventions>`.


Other standards to check for in a PR include:

*  A pull request MUST NOT contain a mix of bug fixes and new features that are not tightly related. If yes, ask the author to split the pull request into separate PRs.
*  If the pull request is not a documentation fix, it must include a :ref:`changelog fragment <collection_changelog_fragments>`. Check the format carefully as follows:

  * New modules and plugins (that are not jinja2 filter and test plugins) do not need changelog fragments.
  * For jinja2 filter and test plugins, check out the `special syntax for changelog fragments <https://github.com/ansible-community/antsibull-changelog/blob/main/docs/changelogs.rst#adding-new-roles-playbooks-test-and-filter-plugins>`_.
  * The changelog content contains useful information for end users of the collection.
  
*  If new files are added with the pull request, they follow the `licensing rules <https://github.com/ansible-collections/overview/blob/main/collection_requirements.rst#licensing>`_.
*  The changes follow the :ref:`Ansible documentation standards <developing_modules_documenting>` and the :ref:`style_guide`.
*  The changes follow the :ref:`Development conventions <developing_modules_best_practices>`.
*  If a new plugin is added, it is one of the `allowed plugin types <https://github.com/ansible-collections/overview/blob/main/collection_requirements.rst#modules-plugins>`_.
*  Documentation, examples, and return sections use FQCNs for the ``M(..)`` :ref:`format macros <module_documents_linking>` when referring to modules.
*  Modules and plugins from ansible-core use ``ansible.builtin.`` as an FQCN prefix when mentioned.
*  When a new option, module, plugin, or return value is added, the corresponding documentation or return sections use ``version_added:`` containing the *collection* version in which they will be first released in.

  * This  is typically the next minor release, sometimes the next major release. For example: if 2.7.5 is the current release, the next minor release will be 2.8.0, and the next major release will be 3.0.0).

*  FQCNs are used for ``extends_documentation_fragment:``, unless the author is referring to doc_fragments from ansible-core.
*  New features have corresponding examples in the :ref:`examples_block`.
*  Return values are documented in the :ref:`return_block`.


Review tests in the PR
----------------------
Review the following if tests are applicable and possible to implement for the changes included in the PR:


*  Where applicable, the pull request has :ref:`testing_integration` and :ref:`testing_units`.
*  All changes are covered. For example, a bug case or a new option separately and in sensible combinations with other options.
*  Integration tests cover ``check_mode`` if supported.
*  Integration tests check the actual state of the system, not only what the module reports. For example, if the module actually changes a file, check that the file was changed by using the ``ansible.builtin.stat`` module..
*  Integration tests check return values, if applicable.


Review for merge commits and breaking changes
---------------------------------------------

*  The pull request does not contain merge commits. See the GitHub warnings at the bottom of the pull request. If merge commits are present, ask the author to rebase the pull request branch.
*  If the pull request contains breaking changes, ask the author and the collection maintainers if it really is needed, and if there is a way not to introduce breaking changes. If breaking changes are present, they MUST only appear in the next major release and MUST NOT appear in a minor or patch release. The only exception is breaking changes caused by security fixes that are absolutely necessary to fix the security issue.

