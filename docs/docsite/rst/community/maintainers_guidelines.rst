.. _maintainer_requirements:

Maintainer responsibilities
===========================

.. contents::
   :depth: 1
   :local:

An Ansible collection maintainer is a contributor trusted by the community who makes significant and regular contributions to the project and who has shown themselves as a specialist in the related area.
Collection maintainers have :ref:`extended permissions<collection_maintainers>` in the collection scope.

Ansible collection maintainers provide feedback, responses, or actions on pull requests or issues to the collection(s) they maintain in a reasonably timely manner. They can also update the contributor guidelines for that collection, in collaboration with the Ansible community team and the other maintainers of that collection.

In general, collection maintainers:

- Act in accordance with the :ref:`code_of_conduct`.
- Subscribe to the collection repository they maintain (click :guilabel:`Watch > All activity` in GitHub).
- Keep README, development guidelines, and other general collections :ref:`maintainer_documentation` relevant.
- Review and commit changes made by other contributors.
- :ref:`Backport <Backporting>` changes to stable branches.
- Address or assign issues to appropriate contributors.
- Release collections.
- Ensure that collections adhere to the `Collection Requirements <https://github.com/ansible-collections/overview/blob/main/collection_requirements.rst>`_,
- Track changes announced in `News for collection contributors and maintainers <https://github.com/ansible-collections/news-for-maintainers>`_ and update a collection in accordance with these changes.
- Subscribe and submit news to the  `Bullhorn newsletter <https://github.com/ansible/community/wiki/News#the-bullhorn>`_.
- :ref:`Build a healthy community <expanding_community>` to increase the number of active contributors and maintainers around collections.
- Revise these guidelines to improve the maintainer experience for yourself and others.

Multiple maintainers can divide responsibilities among each other.

How to become a maintainer
--------------------------

A person interested in becoming a maintainer and satisfying the :ref:`requirements<maintainer_requirements>` may either self-nominate or be nominated by another maintainer.

To nominate a candidate, create a GitHub issue in the relevant collection repository. If there is no response, the repository is not actively maintained, or the current maintainers do not have permissions to add the candidate, please create the issue in the `ansible/community <https://github.com/ansible/community>`_ repository.

Communicating as a collection maintainer
-----------------------------------------

 Maintainers MUST subscribe to the `"Changes impacting collection contributors and maintainers" GitHub repo <https://github.com/ansible-collections/news-for-maintainers>`_ and the `Bullhorn newsletter <https://github.com/ansible/community/wiki/News#the-bullhorn>`_. If you have something important to announce through the newsletter (for example, recent releases), see the `Bullhorn's wiki page <https://github.com/ansible/community/wiki/News#the-bullhorn>`_ to learn how.


Collection contributors and maintainers should also communicate through:

* :ref:`communication_irc` appropriate to their collection, or if none exists, the general community and developer chat channels
* Mailing lists such as `ansible-announce <https://groups.google.com/d/forum/ansible-announce>`_ and `ansible-devel <https://groups.google.com/d/forum/ansible-devel>`_
* Collection project boards, issues, and GitHub discussions in corresponding repositories
* Quarterly Contributor Summits.
* Ansiblefest and local meetups.

See :ref:`communication` for more details on these communication channels.

.. _wg_and_real_time_chat:

Working Group and Real-time Chat Request
----------------------------------------

Here are some techniques for communicating more efficiently and interactively within your community:

* Join existing suitable :ref:`working_group_list` and corresponding real-time chats if exist.
* `Request <https://github.com/ansible/community/blob/main/WORKING-GROUPS.md>`_ a new working group for your project.
* `Create <https://hackmd.io/@ansible-community/community-matrix-faq#How-do-I-create-a-public-community-room>`_ a real-time chat for your working group or `ask <https://github.com/ansible/community/issues/new>`_ the community team to create it and make it official.
* Add information about the working group and related real-time chats to your project's ``README.md`` and to its contributor documentation.
* Encourage contributors to join the chats and add themselves to the working group.

See the :ref:`Communication guide <communication_irc>` to learn more about real-time chat.

Community Topics
----------------

The Community and the `Steering Committee <https://docs.ansible.com/ansible/devel/community/steering/community_steering_committee.html>`_ asynchronously discuss and vote on the `Community Topics <https://github.com/ansible-community/community-topics/issues>`_ which impact the whole project or its parts including collections and packaging.

Share your opinion and vote on the topics to help the community make the best decisions.

.. _expanding_community:

Contributor Summits
-------------------

The quarterly Ansible Contributor Summit is a global event that provides our contributors a great opportunity to meet each other, communicate, share ideas, and see that there are other real people behind the messages on Matrix or Libera Chat IRC, or GitHub. This gives a sense of community. Watch the `Bullhorn newsletter <https://github.com/ansible/community/wiki/News#the-bullhorn>`_ for information when the next contributor summit, invite contributors you know, and take part in the event together.

Weekly community Matrix/IRC meetings
------------------------------------

The Community and the Steering Committee come together at weekly meetings in the ``#ansible-community`` `Libera.Chat IRC <https://docs.ansible.com/ansible/devel/community/communication.html#ansible-community-on-irc>`_ channel or in the bridged `#community:ansible.com <https://matrix.to/#/#community:ansible.com>`_ room on `Matrix <https://docs.ansible.com/ansible/devel/community/communication.html#ansible-community-on-matrix>`_ to discuss important project-scale questions. See the `schedule <https://github.com/ansible/community/blob/main/meetings/README.md#schedule>`_ and join.

Expanding the collection community
===================================

.. note::

  If you discover good ways to expand a community or make it more robust, edit this section with your ideas to share with other collection maintainers.

Here are some ways you can expand the community around your collection:

  * Give :ref:`newcomers a positive first experience <collection_new_contributors>`.
  * Offer them to join related :ref:`real-time chats <wg_and_real_time_chat>`.
  * Have :ref:`good documentation <maintainer_documentation>` with guidelines for new contributors.
  * Make people feel welcome personally and individually.
  * Use labels to show easy fixes and leave non-critical easy fixes to newcomers and offer to mentor them.
  * Be responsive in issues, PRs and other communication.
  * Conduct PR days regularly.
  * Maintain a zero-tolerance policy towards behavior violating the :ref:`code_of_conduct`.
  * Put information about how people can register code of conduct violations in your ``README`` and ``CONTRIBUTING`` files.
  * Include quick ways contributors can help and other documentation in your ``README``.
  * Add and keep updated the ``CONTRIBUTORS`` and ``MAINTAINERS`` files.
  * Create a pinned issue to announce that the collection welcomes new maintainers and contributors.
  * Look for new maintainers among active contributors.
  * Announce that your collection welcomes new maintainers.
  * Take part and congratulate new maintainers in Contributor Summits.


.. _collection_new_contributors:

Encouraging new contributors
-----------------------------

Easy-fix items are the best way to attract and mentor new contributors. You should triage incoming issues to mark them with labels such as ``easyfix``, ``waiting_on_contributor``, and ``docs``. where appropriate. Do not fix these trivial non-critical bugs yourself. Instead, mentor a person who wants to contribute.

For some easy-fix issues, you could ask the issue reporter whether they want to fix the issue themselves providing the link to a quick start guide for creating PRs.

Conduct pull request days regularly. You could plan PR days, for example, on the last Friday of every month when you and other maintainers go through all open issues and pull requests focusing on old ones, asking people if you can help, and so on. If there are pull requests that look abandoned (for example, there is no response on your help offers since the previous PR day), announce that anyone else interested can complete the pull request.

Promote active contributors satisfying :ref:`requirements<maintainer_requirements>` to maintainers. Revise contributors' activity regularly.

If your collection found new maintainers, announce that fact in the `Bullhorn newsletter <https://github.com/ansible/community/wiki/News#the-bullhorn>`_ and during the next Contributor Summit congratulating and thanking them for the work done. You can mention all the people promoted since the previous summit. Remember to invite the other maintainers to the Summit in advance.

Some other general guidelines to encourage contributors:

* Welcome the author and thank them for the issue or pull request.
* If there is a non-crucial easy-fix bug reported, politely ask the author to fix it themselves providing a link to :ref:`collection_quickstart`.
* When suggesting changes, try to use questions, not statements.
* When suggesting mandatory changes, do it as politely as possible providing documentation references.
* If your suggestion is optional or a matter of personal preference, please say it explicitly.
* When asking for adding tests or for complex code refactoring, say that the author is welcome to ask for clarifications and help if they need it.
* If somebody suggests a good idea, mention it or put a thumbs up.
* After merging, thank the author and reviewers for their time and effort.

See the :ref:`review_checklist` for a list of items to check before you merge a PR.

.. _maintainer_documentation:

Maintaining good collection documentation
==========================================

Maintainers look after the collection documentation to ensure it matches the :ref:`style_guide`. This includes keeping the following documents accurate and updated regularly:

* Collection module and plugin documentation that adheres to the :ref:`Ansible documentation format <module_documenting>`.
* Collection user guides that follow the :ref:`Collection documentation format <collections_doc_dir>`.
* Repository files that includes at least a ``README`` and ``CONTRIBUTING`` file.

A good ``README`` includes a description of the collection, a link to the :ref:`code_of_conduct`, and details on how to contribute or a pointer to the ``CONTRIBUTING`` file. If your collection is a part of Ansible (is shipped with Ansible package), highlight that fact at the top of the collection's ``README``.

 The ``CONTRIBUTING`` file includes all the details or links to the details on how a new or continuing contributor can contribute to this collection. The ``CONTRIBUTING`` file should include:

* Information or links to new contributor guidelines, such as a quick start on opening PRs.
* Information or links to contributor requirements, such as unit and integration test requirements.

You can optionally include a ``CONTRIBUTORS`` and ``MAINTAINERS`` file to list the collection contributors and maintainers.
