|PyPI version| |Docs badge| |Build Status|

*******
Ansible
*******

Ansible is a radically simple IT automation system. It handles
configuration-management, application deployment, cloud provisioning,
ad-hoc task-execution, and multinode orchestration -- including
trivializing things like zero-downtime rolling updates with load
balancers.

Read the documentation and more at https://ansible.com/

You can find installation instructions
`here <https://docs.ansible.com/intro_getting_started.html>`_ for a
variety of platforms.

Most users should probably install a released version of Ansible from ``pip``, a package manager or
our `release repository <https://releases.ansible.com/ansible/>`_. `Officially supported
<https://www.ansible.com/ansible-engine>`_ builds of Ansible are also available. Some power users
run directly from the development branch - while significant efforts are made to ensure that
``devel`` is reasonably stable, you're more likely to encounter breaking changes when running
Ansible this way.

Design Principles
=================

*  Have a dead simple setup process and a minimal learning curve
*  Manage machines very quickly and in parallel
*  Avoid custom-agents and additional open ports, be agentless by
   leveraging the existing SSH daemon
*  Describe infrastructure in a language that is both machine and human
   friendly
*  Focus on security and easy auditability/review/rewriting of content
*  Manage new remote machines instantly, without bootstrapping any
   software
*  Allow module development in any dynamic language, not just Python
*  Be usable as non-root
*  Be the easiest IT automation system to use, ever.

Get Involved
============

*  Read `Community
   Information <https://docs.ansible.com/community.html>`_ for all
   kinds of ways to contribute to and interact with the project,
   including mailing list information and how to submit bug reports and
   code to Ansible.
*  All code submissions are done through pull requests. Take care to
   make sure no merge commits are in the submission, and use
   ``git rebase`` vs ``git merge`` for this reason. If submitting a
   large code change (other than modules), it's probably a good idea to
   join ansible-devel and talk about what you would like to do or add
   first to avoid duplicate efforts. This not only helps everyone
   know what's going on, it also helps save time and effort if we decide
   some changes are needed.
*  Users list:
   `ansible-project <https://groups.google.com/group/ansible-project>`_
*  Development list:
   `ansible-devel <https://groups.google.com/group/ansible-devel>`_
*  Announcement list:
   `ansible-announce <https://groups.google.com/group/ansible-announce>`_
   -- read only
*  irc.freenode.net: #ansible

Branch Info
===========

*  Releases are named after Led Zeppelin songs. (Releases prior to 2.0
   were named after Van Halen songs.)
*  The devel branch corresponds to the release actively under
   development.
*  Various release-X.Y branches exist for previous releases.
*  We'd love to have your contributions, read `Community
   Information <https://docs.ansible.com/community.html>`_ for notes on
   how to get started.

Authors
=======

Ansible was created by `Michael DeHaan <https://github.com/mpdehaan>`_
(michael.dehaan/gmail/com) and has contributions from over 1000 users
(and growing). Thanks everyone!

Ansible is sponsored by `Ansible, Inc <https://ansible.com>`_

License
=======

GNU General Public License v3.0

See `COPYING <COPYING>`_ to see the full text.

.. |PyPI version| image:: https://img.shields.io/pypi/v/ansible.svg
   :target: https://pypi.org/project/ansible
.. |Docs badge| image:: https://img.shields.io/badge/docs-latest-brightgreen.svg
   :target: http://docs.ansible.com/ansible
.. |Build Status| image:: https://api.shippable.com/projects/573f79d02a8192902e20e34b/badge?branch=devel
   :target: https://app.shippable.com/projects/573f79d02a8192902e20e34b
