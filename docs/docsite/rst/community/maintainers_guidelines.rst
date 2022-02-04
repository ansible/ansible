.. _maintainers_general:


Maintainer responsibilities
===========================

Ansible collection maintainers provide feedback, responses, or actions on pull requests or issues to the collection(s) they maintain in a reasonably timely manner. You can also update the contributor guidelines for that collection, in collaboration with the Ansible community team and the other maintainers of that collection.

In general, collection maintainers:

- Keep README, development guidelines, and other general collection :ref:`maintainer_documentation` relevant.
- :ref:`Reviewing` and committing changes made by other contributors.
- :ref:`Backporting` changes to stable branches.
- Address issues either themselves or assign to appropriate contributors.
- Release collections.
- Watch that collections adhere to the `Collection Requirements <https://github.com/ansible-collections/overview/blob/main/collection_requirements.rst>`_,
- Track changes announced in `News for collection contributors and maintainers <https://github.com/ansible-collections/news-for-maintainers>`_ and update a collection in accordance with these changes.
- :ref:`Build a healthy community <expanding_community>` to increase the number of active contributors and maintainers around collections.
- Revise these guidelines to improve the maintainer experience for yourself and others.

.. _maintainer_requirements:

Who is a collection maintainer?
--------------------------------

A collection maintainer is a contributor trusted by the community who makes significant and regular contributions to the project and showed themselves as a specialist in the related area.
Collection maintainers have :ref:`extended permissions<collection_maintainers>` in the collection scope.

Maintainers act in accordance with the :ref:`code_of_conduct` and also:

- Are responsive to issues and pull requests.
- Have read these guidelines and the linked documents.
- Are subscribed to:

  + The collection repository they maintain (the ``Watch`` button → ``All activity``).
  + The `News for collection contributors and maintainers <https://github.com/ansible-collections/news-for-maintainers>`_.
  + The `Bullhorn newsletter <https://github.com/ansible/community/wiki/News#the-bullhorn>`_.

Multiple maintainers can divide responsibilities between each other.

How to become a maintainer
--------------------------

A person who is interested in becoming a maintainer and satisfies the :ref:`requirements<maintainer_requirements>` may either self-nominate or be nominated by another maintainer.

To nominate a candidate, please create a GitHub issue in the relevant collection repository. If there is no response, the repository is not actively maintained, or the current maintainers do not have permissions to add the candidate, please create the issue under `ansible/community <https://github.com/ansible/community>`_ repository.

Communication channels
=======================

 Maintainers must subscribe to the `"Changes impacting collection contributors and maintainers" GitHub repo <https://github.com/ansible-collections/news-for-maintainers>`_ and should subscribe to the `Bullhorn newsletter <https://github.com/ansible/community/wiki/News#the-bullhorn>`_.


Collection contributors and maintainers should also communicate through:

* :ref:`communication_irc` appropriate to their collection, or if none exist, the general community and developer chat channels.
* Mailing lists such as `ansible-announce <https://groups.google.com/d/forum/ansible-announce>`_ and `ansible-devel <https://groups.google.com/d/forum/ansible-devel>`_
* Collection project boards, issues, and GitHub discussions in corresponding repositories/
* Quarterly Contributor Summits.
* Ansiblefest and local meetups.

See :ref:`communication` for more details on these communication channels.


.. _expanding_community:

Expanding community
===================

.. note::

  If you discover good ways how to expand a community or make it more robust, please share them with other maintainers through changing this document.

  Here are some ways you can expand the community around your collection:

  * Give newcomers a first positive experience.
  * Have good documentation containing  guidelines for new contributors.
  * Make people feel welcome personally and individually.
  * Use labels to show easy fixes.
  * Leave non-critical easy fixes to newcomers and offer to mentor them.
  * Be responsive in issues, PRs and other communication.
  * Conduct PR days regularly.
  * Maintain a zero-tolerance policy towards behavior violating the :ref:`code_of_conduct`.
  * Put information how people can register code of conduct violations in your ``README`` and ``CONTRIBUTING`` files.
  * Include quick ways contributors can help and other documentation in ``README``.
  * Add and keep updated the ``CONTRIBUTORS`` and ``MAINTAINERS`` files.
  * If the collection is a part of Ansible, mention it in ``README``.
  * Create a pinned issue that the collection welcomes new maintainers and contributors.
  * Look for new maintainers among active contributors.
  * Announce that your collection welcomes new maintainers.
  * Take part and congratulate new maintainers in Contributor Summits.

Increasing the number of active contributors and maintainers
-----------------------------------------------------------

Maintainers are interested in increasing a number of active long-term contributors for a collection they maintain.

Put a note in your ``README`` that the project is actively accepting new contributors.

Contributors are reviewers, issue or pull request authors, testers, maintainers, and all other people who help develop the project.

Every regular contributor was once a newcomer. Make the first experience as positive as possible to encourage the new people coming back.

Good development documentation makes a contributor's life much easier. Get feedback from new contributors if there were things they struggled with when working on their proposals and improve the documentation correspondingly.

Create the ``CONTRIBUTING`` file in your repository. In there, add a link to the `Quick-start guide <create_pr_quick_start_guide.rst>`_ as well as to other guidelines describing things specific to your collection.

Make contributors feel welcome. Greet and thank contributors personally in ``README`` and individually in their proposals.
Thank all participants after merging or closing a proposal.

Be responsive. Respond as quickly as possible. Even if you cannot review a proposal right now, greet and thank the author.

If your collection is not huge, add and keep updated the ``CONTRIBUTORS`` file listing all the contributors including issue reporters and refer to it from your ``README``. You can ask contributors to do it themselves or add a note about this to the development documentation of the collection.

Do not fix trivial non-critical bugs yourself. Instead, mentor a person who would like to contribute.
Mark issues with labels like ``easyfix``, ``waiting_on_contributor``, and ``docs``.
They will let newcomers know where they can find easy wins.

When reviewing an issue, if applicable, ask the author whether they want to fix the issue themselves providing the link to the `Quick-start guide <create_pr_quick_start_guide.rst>`_.

Conduct pull request days regularly. You could plan PR days, for example, in the last Friday of every month when you and other maintainers go through all open issues and pull requests focusing on old ones, asking people if you can help, and so on. If there are pull requests that look abandoned (for example, there is no response on your help offers since the previous PR day), announce that anyone else interested can complete the pull request.

Adopt a zero-tolerance policy towards behavior violating :ref:`code_of_conduct`. Add information to ``README`` how people can complain referring to the `"Policy violations" Code of Conduct section <https://docs.ansible.com/ansible/latest/community/code_of_conduct.html#policy-violations>`_.

Announce that the project needs new contributors and maintainers through available communication channels.

Promote active contributors satisfying :ref:`requirements<Requirements for maintainers>` to maintainers. Revise contributors activity regularly.

If your collection found new maintainers, announce that fact in the `Bullhorn newsletter <https://github.com/ansible/community/wiki/News#the-bullhorn>`_ and during the next Contributor Summit congratulating and thanking them for the work done. You can mention all the people promoted since the previous summit. Remember to invite the other maintainers to the Summit in advance.

Create the ``MAINTAINERS`` file and keep it updated.

Create a pinned issue which announces that the collection needs new maintainers and contributors providing links to the collection's CONTRIBUTING file and other documentation describing how to contribute to and maintain the collection (for example, it could contain a link to these guidelines).

If your collection is a part of Ansible (is shipped with Ansible package), highlight that fact at the top of the collection's README.


.. _maintainer_documentation:

Documentation
=============

Maintainers look after the collection documentation.

In particular, they are watching that documents of the collection scope, like ``README.md``, are relevant and timely updated and that modules / plugins documentation adheres the `Ansible documentation format <https://docs.ansible.com/ansible/devel/dev_guide/developing_modules_documenting.html>`_ and the `Style guide <https://docs.ansible.com/ansible/devel/dev_guide/style_guide/index.html#style-guide>`_.

.. _Reviewing:

Reviewing
=========

Maintainers can accept or reject proposed changes.

Maintainers review code proposals as well as reported issues following the `review checklist <review_checklist.rst>`_ in applicable parts and the recommendations mentioned in the :ref:`Expanding community<Expanding community>` paragraph.

Inclusion in Ansible
====================

If a collection is not included in Ansible (not shipped with Ansible package), maintainers can submit the collection for inclusion by creating a discussion under `ansible-collections/ansible-inclusion repository <https://github.com/ansible-collections/ansible-inclusion>`_. For more information, refer to the `repository's README <https://github.com/ansible-collections/ansible-inclusion/blob/main/README.md>`_.

Stepping down
=============

Maintainers should not step down silently. This is especially important when the collection has one or few active maintainer.

If you feel you don't have time to maintain your collection any more or for a long period of time, to prevent negative consequences for the collection and its community:

- Inform other maintainers about it.
- If the collection is under the ``ansible-collections`` organization, also inform the community team in the ``ansible-community`` `Libera.Chat IRC channel <https://docs.ansible.com/ansible/devel/community/communication.html#irc-channels>`_ or by email ``ansible-community@redhat.com``.
- Look at active contributors in the collection to find new maintainers among them. Discuss the potential candidates with other maintainers or with the community team.
- If you failed to find a replacement, create a pinned issue in the collection which announces that the collection needs new maintainers.
- Make the same announcement through the `Bullhorn newsletter <https://github.com/ansible/community/wiki/News#the-bullhorn>`_.
- Please be around to discuss potential candidates found by other maintainers or by the community team.

You can come back at any moment.
