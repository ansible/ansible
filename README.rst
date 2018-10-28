|PyPI version| |Docs badge| |Chat badge| |Build Status|

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
`here <https://docs.ansible.com/ansible/latest/installation_guide/intro_installation.html>`_ for a
variety of platforms.

Most users should probably install a released version of Ansible from ``pip``, a package manager or
our `release repository <https://releases.ansible.com/ansible/>`_. `Officially supported
<https://www.ansible.com/ansible-engine>`_ builds of Ansible are also available. Some power users
run directly from the development branch - while significant efforts are made to ensure that
``devel`` is reasonably stable, you're more likely to encounter breaking changes when running
Ansible this way.

Design Principles
=================

*  Have a dead simple setup process and a minimal learning curve.
*  Manage machines very quickly and in parallel.
*  Avoid custom-agents and additional open ports, be agentless by
   leveraging the existing SSH daemon.
*  Describe infrastructure in a language that is both machine and human
   friendly.
*  Focus on security and easy auditability/review/rewriting of content.
*  Manage new remote machines instantly, without bootstrapping any
   software.
*  Allow module development in any dynamic language, not just Python.
*  Be usable as non-root.
*  Be the easiest IT automation system to use, ever.

Get Involved
============

*  Read `Community
   Information <https://docs.ansible.com/ansible/latest/community>`_ for all
   kinds of ways to contribute to and interact with the project,
   including mailing list information and how to submit bug reports and
   code to Ansible.
*  All code submissions are done through pull requests to the ``devel`` branch.
*  Feel free to talk to us before making larger changes
   to avoid duplicate efforts. This not only helps everyone
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
*  For the full list of Email Lists, IRC channels see the
   `Communication page <https://docs.ansible.com/ansible/latest/community/communication.html>`_

Branch Info
===========

*  Releases are named after Led Zeppelin songs. (Releases prior to 2.0
   were named after Van Halen songs.)
*  The ``devel`` branch corresponds to the release actively under
   development.
*  The ``stable-2.x`` branches exist for current releases.
*  Various release-X.Y branches exist for previous releases.
*  For information about the active branches see the
   `Ansible release and maintenance <https://docs.ansible.com/ansible/latest/reference_appendices/release_and_maintenance.html>`_ page.
*  We'd love to have your contributions, read the `Community
   Guide <https://docs.ansible.com/ansible/latest/community>`_ for notes on
   how to get started.

Roadmap
=======

Based on team and community feedback, an initial roadmap will be published for a major or minor version (ex: 2.0, 2.1).
Subminor versions will generally not have roadmaps published.

The `Ansible Roadmap page <https://docs.ansible.com/ansible/devel/roadmap/>`_ details what is planned and how to influence the roadmap.

Authors
=======

Ansible was created by `Michael DeHaan <https://github.com/mpdehaan>`_
(michael.dehaan/gmail/com) and has contributions from over 3700 users
(and growing). Thanks everyone!

`Ansible <https://www.ansible.com>`_ is sponsored by `Red Hat, Inc.
<https://www.redhat.com>`_

License
=======

GNU General Public License v3.0

See `COPYING <COPYING>`_ to see the full text.

.. |PyPI version| image:: https://img.shields.io/pypi/v/ansible.svg
   :target: https://pypi.org/project/ansible
.. |Docs badge| image:: https://img.shields.io/badge/docs-latest-brightgreen.svg
   :target: https://docs.ansible.com/ansible/latest/
.. |Build Status| image:: https://api.shippable.com/projects/573f79d02a8192902e20e34b/badge?branch=devel
   :target: https://app.shippable.com/projects/573f79d02a8192902e20e34b
.. |Chat badge| image:: https://img.shields.io/badge/chat-IRC-brightgreen.svg
   :target: https://docs.ansible.com/ansible/latest/community/communication.html
