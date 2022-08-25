.. _communication:

*****************************************
Communicating with the Ansible community
*****************************************

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

To join the community using Matrix, you need two things:

* a Matrix account (from `Matrix.org <https://app.element.io/#/register>`_ or any other Matrix homeserver)
* a `Matrix client <https://matrix.org/clients/>`_ (we recommend `Element Webchat <https://app.element.io>`_)

The Ansible community maintains its own Matrix homeserver at ``ansible.im``, however public registration is currently unavailable.

Matrix chat supports:

* persistence (when you log on, you see all messages since you last logged off)
* edits (so you can fix your typos)
* replies to individual users
* reactions/emojis
* bridging to IRC
* no line limits
* images

The room links in the :ref:`general_channels` will take you directly to the relevant rooms. For more information, see the community-hosted `Matrix FAQ <https://hackmd.io/@ansible-community/community-matrix-faq>`_.

Ansible community on IRC
------------------------

The Ansible community maintains several IRC channels on `irc.libera.chat <https://libera.chat/>`_. To join the community using IRC, you need one thing:

* an IRC client

IRC chat supports:

* no persistence (you only see messages when you are logged on, unless you add a bouncer)
* simple text interface
* bridging from Matrix

Our IRC channels may require you to register your IRC nickname. If you receive an error when you connect or when posting a message, see `libera.chat's Nickname Registration guide <https://libera.chat/guides/registration>`_ for instructions. To find all ``ansible`` specific channels on the libera.chat network, use the following command in your IRC client:

.. code-block:: text

   /msg alis LIST #ansible* -min 5

as described in the `libera.chat docs <https://libera.chat/guides/findingchannels>`_.

.. _general_channels:

General channels
----------------

The clickable links will take you directly to the relevant Matrix room in your browser; room/channel information is also given for use in other clients:

- `Community social room and posting news for the Bullhorn newsletter <https://matrix.to:/#/#social:ansible.com>`_ - ``Matrix: #social:ansible.com | IRC: #ansible-social``
- `General usage and support questions <https://matrix.to:/#/#users:ansible.com>`_ - ``Matrix: #users:ansible.com | IRC: #ansible``
- `Discussions on developer topics and code related to features or bugs <https://matrix.to/#/#devel:ansible.com>`_ - ``Matrix: #devel:ansible.com | IRC: #ansible-devel``
- `Discussions on community and collections related topics <https://matrix.to:/#/#community:ansible.com>`_ - ``Matrix: #community:ansible.com | IRC: #ansible-community``
- `For public community meetings <https://matrix.to/#/#meeting:ansible.im>`_ - ``Matrix: #meeting:ansible.im | IRC: #ansible-meeting``
   - We will generally announce these on one or more of the above mailing lists. See the `meeting schedule and agenda page <https://github.com/ansible/community/blob/main/meetings/README.md>`_

.. _working_group_list:

Working groups
--------------

Many of our community `Working Groups <https://github.com/ansible/community/wiki#working-groups>`_ meet in chat. If you want to get involved in a working group, join the Matrix room or IRC channel where it meets or comment on the agenda.

- `Amazon (AWS) Working Group <https://github.com/ansible/community/wiki/AWS>`_ - Matrix: `#aws:ansible.com <https://matrix.to:/#/#aws:ansible.com>`_ | IRC: ``#ansible-aws``
- `Ansible Lockdown Working Group <https://github.com/ansible/community/wiki/Lockdown>`_ (`Security playbooks/roles <https://github.com/ansible/ansible-lockdown>`_) - Matrix: `#lockdown:ansible.com <https://matrix.to:/#/#lockdown:ansible.com>`_ | IRC: ``#ansible-lockdown``
- `AWX Working Group <https://github.com/ansible/awx>`_ - Matrix: `#awx:ansible.com <https://matrix.to:/#/#awx:ansible.com>`_ | IRC: ``#ansible-awx``
- `Azure Working Group <https://github.com/ansible/community/wiki/Azure>`_ - Matrix: `#azure:ansible.com <https://matrix.to:/#/#azure:ansible.com>`_ | IRC: ``#ansible-azure``
- `Community Working Group <https://github.com/ansible/community/wiki/Community>`_ (including Meetups) - Matrix: `#community:ansible.com <https://matrix.to:/#/#community:ansible.com>`_ | IRC: ``#ansible-community``
- `Container Working Group <https://github.com/ansible/community/wiki/Container>`_ - Matrix: `#container:ansible.com <https://matrix.to:/#/#container:ansible.com>`_ | IRC: ``#ansible-container``
- `Contributor Experience Working Group <https://github.com/ansible/community/wiki/Contributor-Experience>`_ - Matrix: `#community:ansible.com <https://matrix.to:/#/#community:ansible.com>`_ | IRC: ``#ansible-community``
- `DigitalOcean Working Group <https://github.com/ansible/community/wiki/Digital-Ocean>`_ - Matrix: `#digitalocean:ansible.im <https://matrix.to:/#/#digitalocean:ansible.im>`_ | IRC: ``#ansible-digitalocean``
- `Diversity Working Group <https://github.com/ansible/community/wiki/Diversity>`_ - Matrix: `#diversity:ansible.com <https://matrix.to:/#/#diversity:ansible.com>`_ | IRC: ``#ansible-diversity``
- `Docker Working Group <https://github.com/ansible/community/wiki/Docker>`_ - Matrix: `#devel:ansible.com <https://matrix.to:/#/#devel:ansible.com>`_ | IRC: ``#ansible-devel``
- `Documentation Working Group <https://github.com/ansible/community/wiki/Docs>`_ - Matrix: `#docs:ansible.com <https://matrix.to:/#/#docs:ansible.com>`_ | IRC: ``#ansible-docs``
- `Galaxy Working Group <https://github.com/ansible/community/wiki/Galaxy>`_ - Matrix: `#galaxy:ansible.com <https://matrix.to:/#/#galaxy:ansible.com>`_ | IRC: ``#ansible-galaxy``
- `JBoss Working Group <https://github.com/ansible/community/wiki/JBoss>`_ - Matrix: `#jboss:ansible.com <https://matrix.to:/#/#jboss:ansible.com>`_ | IRC: ``#ansible-jboss``
- `Kubernetes Working Group <https://github.com/ansible/community/wiki/Kubernetes>`_ - Matrix: `#kubernetes:ansible.com <https://matrix.to:/#/#kubernetes:ansible.com>`_ | IRC: ``#ansible-kubernetes``
- `Linode Working Group <https://github.com/ansible/community/wiki/Linode>`_ - Matrix: `#linode:ansible.com <https://matrix.to:/#/#linode:ansible.com>`_ | IRC: ``#ansible-linode``
- `Molecule Working Group <https://github.com/ansible/community/wiki/Molecule>`_ (`testing platform for Ansible playbooks and roles <https://molecule.readthedocs.io>`_) - Matrix: `#molecule:ansible.im <https://matrix.to:/#/#molecule:ansible.im>`_ | IRC: ``#ansible-molecule``
- `Network Working Group <https://github.com/ansible/community/wiki/Network>`_ - Matrix: `#network:ansible.com <https://matrix.to:/#/#network:ansible.com>`_ | IRC: ``#ansible-network``
- `PostgreSQL Working Group <https://github.com/ansible-collections/community.postgresql/wiki/PostgreSQL-Working-Group>`_ - Matrix: `#postgresql:ansible.com <https://matrix.to:/#/#postgresql:ansible.com>`_
- `Remote Management Working Group <https://github.com/ansible/community/issues/409>`_ - Matrix: `#devel:ansible.com <https://matrix.to:/#/#devel:ansible.com>`_ | IRC: ``#ansible-devel``
- `Testing Working Group <https://github.com/ansible/community/wiki/Testing>`_  - Matrix: `#devel:ansible.com <https://matrix.to:/#/#devel:ansible.com>`_ | IRC: ``#ansible-devel``
- `VMware Working Group <https://github.com/ansible/community/wiki/VMware>`_ - Matrix: `#vmware:ansible.com <https://matrix.to:/#/#vmware:ansible.com>`_ | IRC: ``#ansible-vmware``
- `Windows Working Group <https://github.com/ansible/community/wiki/Windows>`_ - Matrix: `#windows:ansible.com <https://matrix.to:/#/#windows:ansible.com>`_ | IRC: ``#ansible-windows``
- `Ansible developer tools Group <https://github.com/ansible/community/wiki/Ansible-developer-tools>`_ - Matrix: `#devtools:ansible.com <https://matrix.to/#/#devtools:ansible.com>`_ | IRC: ``#ansible-devtools``

Want to `form a new Working Group <https://github.com/ansible/community/blob/main/WORKING-GROUPS.md>`_?

Regional and Language-specific channels
---------------------------------------

- Comunidad Ansible en español - Matrix: `#espanol:ansible.im <https://matrix.to:/#/#espanol:ansible.im>`_ | IRC: ``#ansible-es``
- Communauté française d'Ansible - Matrix: `#francais:ansible.im <https://matrix.to:/#/#francais:ansible.im>`_ | IRC: ``#ansible-fr``
- Communauté suisse d'Ansible - Matrix: `#suisse:ansible.im <https://matrix.to:/#/#suisse:ansible.im>`_ | IRC: ``#ansible-zh``
- European Ansible Community - Matrix: `#europe:ansible.im <https://matrix.to:/#/#europe:ansible.im>`_ | IRC: ``#ansible-eu``

Meetings on chat
----------------

The Ansible community holds regular meetings on various topics on Matrix/IRC, and anyone who is interested is invited to participate. For more information about Ansible meetings, consult the `meeting schedule and agenda page <https://github.com/ansible/community/blob/main/meetings/README.md>`_.

Ansible Community Topics
========================

The `Ansible Community Steering Committee <https://docs.ansible.com/ansible/devel/community/steering/community_steering_committee.html>`_ uses the `community-topics repository <https://github.com/ansible-community/community-topics/issues>`_ to asynchronously discuss with the Community and vote on Community topics in corresponding issues.

Create a new issue in the `repository <https://github.com/ansible-community/community-topics/issues>`_ if you want to discuss an idea that impacts any of the following:

* Ansible Community
* Community collection best practices and `requirements <https://github.com/ansible-collections/overview/blob/main/collection_requirements.rst>`_
* `Community collection inclusion policy <https://github.com/ansible-collections/ansible-inclusion/blob/main/README.md>`_
* `The Community governance <https://docs.ansible.com/ansible/devel/community/steering/community_steering_committee.html>`_
* Other proposals of importance that need the Committee or overall Ansible community attention

Ansible Automation Platform support questions
=============================================

Red Hat Ansible `Automation Platform <https://www.ansible.com/products/automation-platform>`_ is a subscription that contains support, certified content, and tooling for Ansible including content management, a controller, UI and REST API.

If you have a question about Ansible Automation Platform, visit `Red Hat support <https://access.redhat.com/products/red-hat-ansible-automation-platform/>`_ rather than using a chat channel or the general project mailing list.

The Bullhorn
============

**The Bullhorn** is our newsletter for the Ansible contributor community. Please `subscribe <https://eepurl.com/gZmiEP>`_ to receive it.

If you have any content you would like to share, please `contribute/suggest it <https://github.com/ansible/community/wiki/News#the-bullhorn>`_ for upcoming releases.

If you have any questions, please reach out to us at ``the-bullhorn@redhat.com``.

Read past issues on the official Bullhorn's `wiki page <https://github.com/ansible/community/wiki/News#the-bullhorn>`_.
