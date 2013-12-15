[![PyPI version](https://badge.fury.io/py/ansible.png)](http://badge.fury.io/py/ansible)

Ansible
=======

Ansible is a radically simple configuration-management, deployment, task-execution, and
multinode orchestration framework.

Read the documentation and more at http://ansibleworks.com/

Many users run straight from the development branch (it's generally fine to do so), but you might also wish to consume a release.  You can find 
instructions [here](http://ansibleworks.com/docs/intro_getting_started.html) for a variety of platforms.  If you want a tarball of the last release, go to 
http://ansibleworks.com/releases/ and you can also install with pip.

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

   * Read [Contributing.md](https://github.com/ansible/ansible/blob/devel/CONTRIBUTING.md) for all kinds of ways to contribute to and interact with the project, including mailing list information and how to submit bug reports and code to Ansible.  
   * When submitting a bug report, include 1) the output of 'ansible --version', 2) what you expected to happen, 3) what actually happened, and 4) any relevant commands and output.
   * All code submissions are done through pull requests.  Take care to make sure no merge commits are in the submission, and use "git rebase" vs "git merge" for this reason.  If submitting a large code change (other than modules), it's probably a good idea to join ansible-devel and talk about what you would like to do or add first and to avoid duplicate efforts.  This not only helps everyone know what's going on, it also helps save time and effort if we decide some changes are needed.
   * irc.freenode.net: #ansible

Branch Info
===========

   * Releases are named after Van Halen songs.
   * The devel branch corresponds to the release actively under development.
   * Various release-X.Y branches exist for previous releases
   * We'd love to have your contributions, read "CONTRIBUTING.md" for process notes.

Author
======

Michael DeHaan -- michael@ansibleworks.com

[AnsibleWorks](http://ansibleworks.com)

