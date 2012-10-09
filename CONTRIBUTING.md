Contributing to Ansible
=======================

It is required that you read the following information to learn how to contribute to this project.

Branch Info
===========

Here's how to understand the branches.

   * The devel branch corresponds to the latest ongoing release
   * Various release-X.Y branches exist for previous releases
   * All feature work happens on the development branch.
   * Major bug fixes will be made to the last release branch only
   * See CHANGELOG.md for release notes to track each release.

Patch Instructions
==================

Contributions to the core and modules are greatly welcome.

   * Required Process:
       * Submit github pull requests to the "ansible/devel" branch for features
       * Fixes for bugs may also be submitted to "ansible/release-X.Y" for the last release
       * Make sure "make tests" passes before submitting any requests.
   * Bonus points:
       * Joining the mailing list
       * Fixing bugs instead of sending bug reports.
       * Using squash merges
       * Updating the "rst/*" files in the "docsite/" directory and "docs/" manpage content
       * Adding more unit tests
   * Avoid:
       * Sending patches to the mailing list directly.
       * Sending feature pull requests to the 'release' branch instead of the devel branch
       * Sending pull requests to mpdehaan's personal ansible fork.
       * Sending pull requests about more than one feature in the same pull request.
       * Whitespace restructuring
       * Large scale refactoring without a discussion on the list

Coding Standards
================

We're not too strict on style considerations, but we require:

   * python 2.6 compliant code, unless in ansible modules, then python *2.4* compliant code (no 'with', etc)
   * 4-space indents, no tabs except in Makefiles
   * under_scores for method names and variables, not camelCase
   * GPLv3 license headers on all files, with copyright on new files with your name on it
   * no single-line if statements, deeply nested list comprehensions, or clever use of metaclasses -- keep it simple
   * comments where appropriate

Contributors License Agreement
==============================

By contributing you agree that these contributions are your own (or approved by your employer) and you grant a full, complete, irrevocable
copyright license to all users and developers of the project, present and future, persusant to the license of the project.



