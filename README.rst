|PyPI version| |Docs badge| |Chat badge| |Build Status| |Code Of Conduct| |Mailing Lists| |License|

*******
Ansible
*******

Ansible is a radically simple IT automation system. It handles
configuration management, application deployment, cloud provisioning,
ad-hoc task execution, network automation, and multi-node orchestration. Ansible makes complex
changes like zero-downtime rolling updates with load balancers easy. More information on `the Ansible website <https://ansible.com/>`_.

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

Use Ansible
===========

You can install a released version of Ansible via ``pip``, a package manager, or
our `release repository <https://releases.ansible.com/ansible/>`_. See our
`installation guide <https://docs.ansible.com/ansible/latest/installation_guide/intro_installation.html>`_ for details on installing Ansible
on a variety of platforms.

Red Hat offers supported builds of `Ansible Engine <https://www.ansible.com/ansible-engine>`_.

Power users and developers can run the ``devel`` branch, which has the latest
features and fixes, directly. Although it is reasonably stable, you are more likely to encounter
breaking changes when running the ``devel`` branch. We recommend getting involved
in the Ansible community if you want to run the ``devel`` branch.

Get Involved
============

*  Read `Community
   Information <https://docs.ansible.com/ansible/latest/community>`_ for all
   kinds of ways to contribute to and interact with the project,
   including mailing list information and how to submit bug reports and
   code to Ansible.
*  Join a `Working Group
   <https://github.com/ansible/community/wiki>`_, an organized community devoted to a specific technology domain or platform.
*  Submit a proposed code update through a pull request to the ``devel`` branch.
*  Talk to us before making larger changes
   to avoid duplicate efforts. This not only helps everyone
   know what is going on, it also helps save time and effort if we decide
   some changes are needed.
*  For a list of email lists, IRC channels and Working Groups, see the
   `Communication page <https://docs.ansible.com/ansible/latest/community/communication.html>`_

Branch Info
===========

*  The ``devel`` branch corresponds to the release actively under development.
*  The ``stable-2.X`` branches correspond to stable releases.
*  Create a branch based on ``devel`` and set up a `dev environment <https://docs.ansible.com/ansible/latest/dev_guide/developing_modules_general.html#common-environment-setup>`_ if you want to open a PR.
*  See the `Ansible release and maintenance <https://docs.ansible.com/ansible/latest/reference_appendices/release_and_maintenance.html>`_ page for information about active branches.

Roadmap
=======

Based on team and community feedback, an initial roadmap will be published for a major or minor version (ex: 2.7, 2.8).
The `Ansible Roadmap page <https://docs.ansible.com/ansible/devel/roadmap/>`_ details what is planned and how to influence the roadmap.

Authors
=======

Ansible was created by `Michael DeHaan <https://github.com/mpdehaan>`_
and has contributions from over 4000 users (and growing). Thanks everyone!

`Ansible <https://www.ansible.com>`_ is sponsored by `Red Hat, Inc.
<https://www.redhat.com>`_

License
=======

GNU General Public License v3.0 or later

See `COPYING <COPYING>`_ to see the full text.

.. |PyPI version| image:: https://img.shields.io/pypi/v/ansible.svg
   :target: https://pypi.org/project/ansible
.. |Docs badge| image:: https://img.shields.io/badge/docs-latest-brightgreen.svg
   :target: https://docs.ansible.com/ansible/latest/
.. |Build Status| image:: https://dev.azure.com/ansible/ansible/_apis/build/status/CI?branchName=stable-2.9
   :target: https://dev.azure.com/ansible/ansible/_build/latest?definitionId=20&branchName=stable-2.9
.. |Chat badge| image:: https://img.shields.io/badge/chat-IRC-brightgreen.svg
   :target: https://docs.ansible.com/ansible/latest/community/communication.html
.. |Code Of Conduct| image:: https://img.shields.io/badge/code%20of%20conduct-Ansible-silver.svg
   :target: https://docs.ansible.com/ansible/latest/community/code_of_conduct.html
   :alt: Ansible Code of Conduct
.. |Mailing Lists| image:: https://img.shields.io/badge/mailing%20lists-Ansible-orange.svg
   :target: https://docs.ansible.com/ansible/latest/community/communication.html#mailing-list-information
   :alt: Ansible mailing lists
.. |License| image:: https://img.shields.io/badge/license-GPL%20v3.0-brightgreen.svg
   :target: COPYING
   :alt: Repository License
