Ansible
=======

Ansible is a radically simple configuration-management, deployment, task-execution, and
multinode orchestration framework.

Read the documentation at http://ansible.github.com

Design Principles
=================

   * Dead simple setup
   * Super fast & parallel by default
   * No server or client daemons; use existing SSHd
   * No additional software required on client boxes
   * Modules can be written in ANY language
   * Awesome API for creating very powerful distributed scripts
   * Be usable as non-root
   * The easiest config management system to use, ever.

Get Involved
============

   * [ansible-project mailing list](http://groups.google.com/group/ansible-project)
   * irc.freenode.net: #ansible

Branch Info
===========

   * Releases are named after Van Halen songs.
   * The devel branch corresponds to release 0.7, "Panama".
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
       * Updating the "rst/*" files in the docs project and "docs/" manpage content
       * Adding more unit tests
   * Avoid:
       * Sending patches to the mailing list directly.
       * Sending feature pull requests to the 'release' branch instead of the devel branch
       * Sending pull requests to mpdehaan's personal ansible fork.


Author
======

Michael DeHaan -- michael.dehaan@gmail.com

[http://michaeldehaan.net](http://michaeldehaan.net/)


