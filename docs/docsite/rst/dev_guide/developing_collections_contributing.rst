.. _hacking_collections:

***************************
Contributing to collections
***************************

If you want to add functionality to an existing collection, modify a collection you are using to fix a bug, or change the behavior of a module in a collection, clone the git repository for that collection and make changes on a branch. You can combine changes to a collection with a local checkout of Ansible (``source hacking/env-setup``).
You should first check the collection repository to see if it has specific contribution guidelines. These are typically listed in the README.md or CONTRIBUTING.md files within the repository.
Contributing to a collection: community.general
===============================================

This section describes the process for `community.general <https://github.com/ansible-collections/community.general/>`_. To contribute to other collections, replace the folder names ``community`` and ``general`` with the namespace and collection name of a different collection.

We assume that you have included ``~/dev/ansible/collections/`` in :ref:`COLLECTIONS_PATHS`, and if that path mentions multiple directories, that you made sure that no other directory earlier in the search path contains a copy of ``community.general``. Create the directory ``~/dev/ansible/collections/ansible_collections/community``, and in it clone `the community.general Git repository <https://github.com/ansible-collections/community.general/>`_ or a fork of it into the folder ``general``::

    mkdir -p ~/dev/ansible/collections/ansible_collections/community
    cd ~/dev/ansible/collections/ansible_collections/community
    git clone git@github.com:ansible-collections/community.general.git general

If you clone a fork, add the original repository as a remote ``upstream``::

    cd ~/dev/ansible/collections/ansible_collections/community/general
    git remote add upstream git@github.com:ansible-collections/community.general.git

Now you can use this checkout of ``community.general`` in playbooks and roles with whichever version of Ansible you have installed locally, including a local checkout of ``ansible/ansible``'s ``devel`` branch.

For collections hosted in the ``ansible_collections`` GitHub org, create a branch and commit your changes on the branch. When you are done (remember to add tests, see :ref:`testing_collections`), push your changes to your fork of the collection and create a Pull Request. For other collections, especially for collections not hosted on GitHub, check the ``README.md`` of the collection for information on contributing to it.

.. seealso::

   :ref:`collections`
       Learn how to install and use collections.
   :ref:`contributing_maintained_collections`
       Guidelines for contributing to selected collections
   `Mailing List <https://groups.google.com/group/ansible-devel>`_
       The development mailing list
   `irc.freenode.net <http://irc.freenode.net>`_
       #ansible IRC chat channel
