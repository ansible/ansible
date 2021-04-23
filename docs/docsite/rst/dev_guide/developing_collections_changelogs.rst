.. _collection_changelogs:

***************************************************************
Generating changelogs and porting guide entries in a collection
***************************************************************

You can create and share changelog and porting guide entries for your collection. If your collection is part of the Ansible Community package, we recommend that you use the `antsibull-changelog <https://github.com/ansible-community/antsibull-changelog>`_ tool to generate Ansible-compatible changelogs. The Ansible changelog uses the output of this tool to collate all the collections included in an Ansible release into one combined changelog for the release.

.. note::

	Ansible here refers to the Ansible 2.10 or later release that includes a curated set of collections.

.. contents::
   :local:
   :depth: 2

Understanding antsibull-changelog
=================================

The ``antsibull-changelog`` tool allows you to create and update changelogs for Ansible collections that are compatible with the combined Ansible changelogs. This is an update to the changelog generator used in prior Ansible releases. The tool adds three new changelog fragment categories: ``breaking_changes``, ``security_fixes`` and ``trivial``. The tool also generates the ``changelog.yaml`` file that Ansible uses to create the combined ``CHANGELOG.rst`` file and Porting Guide for the release.

See :ref:`changelogs_how_to` and the `antsibull-changelog documentation <https://github.com/ansible-community/antsibull-changelog/tree/main/docs>`_ for complete details.

.. note::

	The collection maintainers set the changelog policy for their collections. See the individual collection contributing guidelines for complete details.

Generating changelogs
---------------------

To initialize changelog generation:

#. Install ``antsibull-changelog``: :code:`pip install antsibull-changelog`.
#. Initialize changelogs for your repository: :code:`antsibull-changelog init <path/to/your/collection>`.
#. Optionally, edit the ``changelogs/config.yaml`` file to customize the location of the generated changelog ``.rst`` file or other options. See `Bootstrapping changelogs for collections <https://github.com/ansible-community/antsibull-changelog/blob/main/docs/changelogs.rst#bootstrapping-changelogs-for-collections>`_ for details.

To generate changelogs from the changelog fragments you created:

#. Optionally, validate your changelog fragments: :code:`antsibull-changelog lint`.
#. Generate the changelog for your release: :code:`antsibull-changelog release [--version version_number]`.

.. note::

  Add the  ``--reload-plugins`` option if you ran the ``antsibull-changelog release`` command previously and the version of the collection has not changed. ``antsibull-changelog`` caches the information on all plugins and does not update its cache until the collection version changes.

Porting Guide entries from changelog fragments
----------------------------------------------

The Ansible changelog generator automatically adds several changelog fragment categories to the Ansible Porting Guide:

* ``major_changes``
* ``breaking_changes``
* ``deprecated_features``
* ``removed_features``

Including collection changelogs into Ansible
=============================================

If your collection is part of Ansible, use one of the following three options  to include your changelog into the Ansible release changelog:

* Use the ``antsibull-changelog`` tool.

* If are not using this tool, include the properly formatted ``changelog.yaml`` file  into your collection. See the `changelog.yaml format <https://github.com/ansible-community/antsibull-changelog/blob/main/docs/changelog.yaml-format.md>`_ for details.

* Add a link to own changelogs or release notes in any format by opening an issue at https://github.com/ansible-community/ansible-build-data/ with the HTML link to that information.

.. note::

   For the first two options, Ansible pulls the changelog details from Galaxy so your changelogs must be included in the collection version on Galaxy that is included in the upcoming Ansible release.

.. seealso::

   :ref:`collections`
       Learn how to install and use collections.
   :ref:`contributing_maintained_collections`
       Guidelines for contributing to selected collections
   `Mailing List <https://groups.google.com/group/ansible-devel>`_
       The development mailing list
   `irc.freenode.net <http://irc.freenode.net>`_
       #ansible IRC chat channel
