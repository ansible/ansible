GitHub Admins
=============

.. contents:: Topics

GitHub Admins have more permissions on GitHub than normal contributors.  There are
a few responsibilities that come with that increased power.


Add and Remove Committers
-------------------------

The Ansible Team will periodically review who is actively contributing to Ansible to grant or revoke
contributors' ability to commit on their own.  GitHub Admins are the people who have the power to
actually manage the GitHub permissions.


Change Branch Permissions for Release
-------------------------------------

When we make releases we make people go through a :ref:`release_managers` to push commits to that
branch.  The GitHub admins are responsible for setting the branch so only the Release Manager can
commit to the branch when the release process reaches that stage and later opening the branch once
the release has been made.  The Release manager will let the GitHub Admin know when this needs to be
done.

.. seealso:: The `GitHub Admin Process Docs
    <https://github.com/ansible/ansible/blob/devel/hacking/release-branches.rst>`_ for instructions
    on how to change branch permissions.
