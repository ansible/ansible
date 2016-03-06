[![PyPI version](https://img.shields.io/pypi/v/ansible.svg)](https://pypi.python.org/pypi/ansible)
[![PyPI downloads](https://img.shields.io/pypi/dm/ansible.svg)](https://pypi.python.org/pypi/ansible)
[![Build Status](https://travis-ci.org/ansible/ansible.svg?branch=devel)](https://travis-ci.org/ansible/ansible)


Ansible
=======

Ansible is a radically simple IT automation system.  It handles configuration-management, application deployment, cloud provisioning, ad-hoc task-execution, and multinode orchestration - including trivializing things like zero downtime rolling updates with load balancers.

Read the documentation and more at http://ansible.com/

Many users run straight from the development branch (it's generally fine to do so), but you might also wish to consume a release.  

You can find instructions [here](http://docs.ansible.com/intro_getting_started.html) for a variety of platforms.  If you decide to go with the development branch, be sure to run `git submodule update --init --recursive` after doing a checkout. 

If you want to download a tarball of a release, go to [releases.ansible.com](http://releases.ansible.com/ansible), though most users use `yum` (using the EPEL instructions linked above), `apt` (using the PPA instructions linked above), or `pip install ansible`.

Design Principles
=================

   * Have a dead simple setup process and a minimal learning curve
   * Manage machines very quickly and in parallel
   * Avoid custom-agents and additional open ports, be agentless by leveraging the existing SSH daemon
   * Describe infrastructure in a language that is both machine and human friendly
   * Focus on security and easy auditability/review/rewriting of content
   * Manage new remote machines instantly, without bootstrapping any software
   * Allow module development in any dynamic language, not just Python
   * Be usable as non-root
   * Be the easiest IT automation system to use, ever.
  
Get Involved
============

   * Read [Community Information](http://docs.ansible.com/community.html) for all kinds of ways to contribute to and interact with the project, including mailing list information and how to submit bug reports and code to Ansible.  
   * All code submissions are done through pull requests.  Take care to make sure no merge commits are in the submission, and use `git rebase` vs `git merge` for this reason.  If submitting a large code change (other than modules), it's probably a good idea to join ansible-devel and talk about what you would like to do or add first and to avoid duplicate efforts.  This not only helps everyone know what's going on, it also helps save time and effort if we decide some changes are needed.
   * Users list: [ansible-project](http://groups.google.com/group/ansible-project)
   * Development list: [ansible-devel](http://groups.google.com/group/ansible-devel)
   * Announcement list: [ansible-announce](http://groups.google.com/group/ansible-announce) - read only
   * irc.freenode.net: #ansible

Branch Info
===========

   * Releases are named after Led Zeppelin songs. (Releases prior to 2.0 were named after Van Halen songs.)
   * The devel branch corresponds to the release actively under development.
   * As of 1.8, modules are kept in different repos, you'll want to follow [core](https://github.com/ansible/ansible-modules-core) and [extras](https://github.com/ansible/ansible-modules-extras)
   * Various release-X.Y branches exist for previous releases.
   * We'd love to have your contributions, read [Community Information](http://docs.ansible.com/community.html) for notes on how to get started.

Authors
=======

Ansible was created by [Michael DeHaan](https://github.com/mpdehaan) (michael.dehaan/gmail/com) and has contributions from over 1000 users (and growing).  Thanks everyone!

Ansible is sponsored by [Ansible, Inc](http://ansible.com)


