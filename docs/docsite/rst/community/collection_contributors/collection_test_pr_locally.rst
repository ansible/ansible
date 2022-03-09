.. _collection_pr_test:

****************************
How to test a collection PR
****************************

Reviewers and issue authors can verify a PR fixes the reported bug by testing the PR locally.

.. contents::
   :local:

.. _collection_prepare_environment:

Prepare your environment
========================

We assume that you use Linux as a work environment (you can use a virtual machine as well) and have ``git`` installed.


1. :ref:`Install Ansible <installation_guide>` or ansible-core.

2. Create the following directories in your home directory:

  .. code:: bash

    mkdir -p ~/ansible_collections/NAMESPACE/COLLECTION_NAME

  For example, if the collection is ``community.general``:

  .. code:: bash

    mkdir -p ~/ansible_collections/community/general

  If the collection is ``ansible.posix``:

  .. code:: bash

    mkdir -p ~/ansible_collections/ansible/posix


3. Clone the forked repository from the author profile to the created path:

  .. code:: bash

    git clone https://github.com/AUTHOR_ACC/COLLECTION_REPO.git ~/ansible_collections/NAMESPACE/COLLECTION_NAME

4. Go to the cloned repository.

  .. code:: bash

    cd ~/ansible_collections/NAMESPACE/COLLECTION_NAME

5. Checkout the PR branch (it can be retrieved from the PR's page):

  .. code:: bash

    git checkout pr_branch


Test the Pull Request
=====================

1. Include `~/ansible_collections` in `COLLECTIONS_PATHS`. See :ref:`COLLECTIONS_PATHS` for details.

2. Run your playbook using the PR branch and verify the PR fixed the bug.

3. Give feedback on the pull request or the linked issue(s).
