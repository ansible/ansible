.. _communication:

*************
Communicating
*************

.. contents::
   :local:

Code of Conduct
===============

All communication and interactions in the Ansible Community are governed by our :ref:`code_of_conduct`. Please read and understand it!

Asking questions over email
===========================

If you want to keep up with Ansible news, need help, or have a question, you can use one of the Ansible mailing lists. Each list covers a particular topic. Read the descriptions here to find the best list for your question.

Your first post to the mailing list will be moderated (to reduce spam), so please allow up to a day or so for your first post to appear.

* `Ansible Announce list <https://groups.google.com/forum/#!forum/ansible-announce>`_ is a read-only list that shares information about new releases of Ansible, and also rare infrequent event information, such as announcements about an upcoming AnsibleFest, which is our official conference series. Worth subscribing to!
* `Ansible AWX List <https://groups.google.com/forum/#!forum/awx-project>`_ is for `Ansible AWX <https://github.com/ansible/awx>`_
* `Ansible Development List <https://groups.google.com/forum/#!forum/ansible-devel>`_ is for questions about developing Ansible modules (mostly in Python), fixing bugs in the Ansible core code, asking about prospective feature design, or discussions about extending Ansible or features in progress.
* `Ansible Lockdown List <https://groups.google.com/forum/#!forum/ansible-lockdown>`_ is for all things related to Ansible Lockdown projects, including DISA STIG automation and CIS Benchmarks.
* `Ansible Outreach List <https://groups.google.com/forum/#!forum/ansible-outreach>`_ help with promoting Ansible and `Ansible Meetups <https://ansible.meetup.com/>`_
* `Ansible Project List <https://groups.google.com/forum/#!forum/ansible-project>`_ is for sharing Ansible tips, answering questions about playbooks and roles, and general user discussion.
* `Molecule Discussions <https://github.com/ansible-community/molecule/discussions>`_ is designed to aid with the development and testing of Ansible roles with Molecule.

The Ansible mailing lists are hosted on Google, but you do not need a Google account to subscribe. To subscribe to a group from a non-Google account, send an email to the subscription address requesting the subscription. For example: ``ansible-devel+subscribe@googlegroups.com``.

.. _communication_irc:

Real-time chat
==============

For real-time interactions, conversations in the Ansible community happen over two chat protocols: Matrix and IRC. We maintain a bridge between Matrix and IRC, so you can choose whichever protocol you prefer. All channels exist in both places. Join a channel any time to ask questions, participate in a Working Group meeting, or just say hello.

Ansible community on Matrix
---------------------------

The Ansible community maintains its own Matrix homeserver at ``ansible.im``. To join the community using Matrix, you need two things:

* a Matrix account (from matrix.org or any other Matrix homeserver)
* a `Matrix client <https://matrix.org/clients/>`_ (we recommend `Element Webchat <https://app.element.io>`_)

Matrix chat supports:

* persistence (when you log on, you see all messages since you last logged off)
* edits (so you can fix your typos)
* replies to individual users
* reactions/emojis
* bridging to IRC
* no line limits
* images

Ansible community on IRC
------------------------

The Ansible community maintains several IRC channels on `irc.libera.chat <https://libera.chat/>`_. To join the community using IRC, you need one thing:

* an IRC client

IRC chat supports:

* no persistence (you only see messages when you are logged on, unless you add a bouncer)
* simple text interface
* bridging from Matrix

Our IRC channels may require you to register your IRC nickname. If you receive an error when you connect, see `libera.chat's Nickname Registration guide <https://libera.chat/guides/registration>`_ for instructions. To find all ``ansible`` specific channels on the libera.chat network, use the following command in your IRC client::

   /msg alis LIST #ansible* -min 5

as described in the `libera.chat docs <https://libera.chat/guides/findingchannels>`_.

General channels
----------------

- ``#ansible`` - For general use questions and support.
- ``#ansible-devel`` - For discussions on developer topics and code related to features or bugs.
- ``#ansible-community`` - For discussions on community and collections related topics.
- ``#ansible-meeting`` - For public community meetings. We will generally announce these on one or more of the above mailing lists. See the `meeting schedule and agenda page <https://github.com/ansible/community/blob/master/meetings/README.md>`_

.. _working_group_list:

Working groups
--------------

Many of our community `Working Groups <https://github.com/ansible/community/wiki#working-groups>`_ meet in chat. If you want to get involved in a working group, join the Matrix room or IRC channel where it meets or comment on the agenda.

- `Amazon (AWS) Working Group <https://github.com/ansible/community/wiki/AWS>`_ - ``#ansible-aws``
- `Ansible Lockdown Working Group <https://github.com/ansible/community/wiki/Lockdown>`_ | `gh/ansible/ansible-lockdown <https://github.com/ansible/ansible-lockdown>`_ - ``#ansible-lockdown``- Security playbooks/roles
- `AWX Working Group <https://github.com/ansible/awx>`_ - ``#ansible-awx``
- `Azure Working Group <https://github.com/ansible/community/wiki/Azure>`_ - ``#ansible-azure``
- `Community Working Group <https://github.com/ansible/community/wiki/Community>`_ - ``#ansible-community`` - Including Meetups
- `Container Working Group <https://github.com/ansible/community/wiki/Container>`_ - ``#ansible-container``
- `Contributor Experience Working Group <https://github.com/ansible/community/wiki/Contributor-Experience>`_ - ``#ansible-community``
- `DigitalOcean Working Group <https://github.com/ansible/community/wiki/Digital-Ocean>`_ - ``#ansible-digitalocean``
- `Diversity Working Group <https://github.com/ansible/community/wiki/Diversity>`_ - ``#ansible-diversity``
- `Docker Working Group <https://github.com/ansible/community/wiki/Docker>`_ - ``#ansible-devel``
- `Documentation Working Group <https://github.com/ansible/community/wiki/Docs>`_- ``#ansible-docs``
- `Galaxy Working Group <https://github.com/ansible/community/wiki/Galaxy>`_ - ``#ansible-galaxy``
- `JBoss Working Group <https://github.com/ansible/community/wiki/JBoss>`_ - ``#ansible-jboss``
- `Kubernetes Working Group <https://github.com/ansible/community/wiki/Kubernetes>`_ - ``#ansible-kubernetes``
- `Lightbulb Training <https://github.com/ansible/lightbulb>`_ - ``#ansible-lightbulb`` - Ansible training
- `Linode Working Group <https://github.com/ansible/community/wiki/Linode>`_ - ``#ansible-linode``
- `Molecule Working Group <https://github.com/ansible/community/wiki/Molecule>`_ | `molecule.io <https://molecule.readthedocs.io>`_ - ``#ansible-molecule`` - testing platform for Ansible playbooks and roles
- `Network Working Group <https://github.com/ansible/community/wiki/Network>`_ - ``#ansible-network``
- `Remote Management Working Group <https://github.com/ansible/community/issues/409>`_ - ``#ansible-devel``
- `Testing Working Group <https://github.com/ansible/community/wiki/Testing>`_  - ``#ansible-devel``
- `VMware Working Group <https://github.com/ansible/community/wiki/VMware>`_ - ``#ansible-vmware``
- `Windows Working Group <https://github.com/ansible/community/wiki/Windows>`_ - ``#ansible-windows``

Want to `form a new Working Group <https://github.com/ansible/community/blob/master/WORKING-GROUPS.md>`_?

Regional and Language-specific channels
---------------------------------------

- ``#ansible-es`` - Channel for Spanish speaking Ansible community.
- ``#ansible-eu`` - Channel for the European Ansible Community.
- ``#ansible-fr`` - Channel for French speaking Ansible community.
- ``#ansiblezh`` - Channel for Zurich/Swiss Ansible community.

Meetings on chat
----------------

The Ansible community holds regular meetings on various topics on Matrix/IRC, and anyone who is interested is invited to participate. For more information about Ansible meetings, consult the `meeting schedule and agenda page <https://github.com/ansible/community/blob/master/meetings/README.md>`_.

Ansible Automation Platform support questions
=============================================

Red Hat Ansible `Automation Platform <https://www.ansible.com/products/automation-platform>`_ is a subscription that contains support, certified content, and tooling for Ansible including content management, a controller, UI and REST API.

If you have a question about Ansible Automation Platform, visit `Red Hat support <https://access.redhat.com/products/red-hat-ansible-automation-platform/>`_ rather than using a chat channel or the general project mailing list.

The Bullhorn
============

**The Bullhorn** is our newsletter for the Ansible developer community.
If you have any questions or content you would like to share, please reach out to us at the-bullhorn@redhat.com, or directly `contribute/suggest content <https://github.com/ansible/community/issues/546>`_ for upcoming issues.

Read past issues `here <https://github.com/ansible/community/wiki/News>`_.

`Subscribe <https://eepurl.com/gZmiEP>`_ to receive it.
