
.. _finding_galaxy_roles:

*************************
Finding roles on Galaxy
*************************

Search the Galaxy database by tags, platforms, author and multiple keywords. For example:

.. code-block:: bash

    $ ansible-galaxy search elasticsearch --author geerlingguy

The search command will return a list of the first 1000 results matching your search:

.. code-block:: text

    Found 2 roles matching your search:

    Name                              Description
    ----                              -----------
    geerlingguy.elasticsearch         Elasticsearch for Linux.
    geerlingguy.elasticsearch-curator Elasticsearch curator for Linux.


Get more information about a role
=================================

Use the ``info`` command to view more detail about a specific role:

.. code-block:: bash

    $ ansible-galaxy info username.role_name

This returns everything found in Galaxy for the role:

.. code-block:: text

    Role: username.role_name
        description: Installs and configures a thing, a distributed, highly available NoSQL thing.
        active: True
        commit: c01947b7bc89ebc0b8a2e298b87ab416aed9dd57
        commit_message: Adding travis
        commit_url: https://github.com/username/repo_name/commit/c01947b7bc89ebc0b8a2e298b87ab
        company: My Company, Inc.
        created: 2015-12-08T14:17:52.773Z
        download_count: 1
        forks_count: 0
        github_branch:
        github_repo: repo_name
        github_user: username
        id: 6381
        is_valid: True
        issue_tracker_url:
        license: Apache
        min_ansible_version: 1.4
        modified: 2015-12-08T18:43:49.085Z
        namespace: username
        open_issues_count: 0
        path: /Users/username/projects/roles
        scm: None
        src: username.repo_name
        stargazers_count: 0
        travis_status_url: https://travis-ci.org/username/repo_name.svg?branch=master
        version:
        watchers_count: 1
