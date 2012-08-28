.. _subversion:

subversion
``````````

.. versionadded:: 0.7

Deploys a subversion repository.

+--------------------+----------+---------+----------------------------------------------------------------------------+
| parameter          | required | default | comments                                                                   |
+====================+==========+=========+============================================================================+
| repo               | yes      |         | The subversion URL to the repository.                                      |
+--------------------+----------+---------+----------------------------------------------------------------------------+
| dest               | yes      |         | Absolute path where the repository should be deployed.                     |
+--------------------+----------+---------+----------------------------------------------------------------------------+
| force              | no       | yes     | If yes, any modified files in the working repository will be               |
|                    |          |         | discarded.  If no, this module will fail if it encounters modified files.  |
+--------------------+----------+---------+----------------------------------------------------------------------------+

Example action from Ansible :doc:`playbooks`::

    subversion repo=svn+ssh://an.example.org/path/to/repo dest=/src/checkout
