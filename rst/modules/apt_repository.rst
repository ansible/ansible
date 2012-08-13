.. _apt_repository:

apt_repository
``````````````

.. versionadded:: 0.7

Manages apt repositores

+--------------------+----------+---------+----------------------------------------------------------------------------+
| parameter          | required | default | comments                                                                   |
+====================+==========+=========+============================================================================+
| repo               | yes      |         | The repository name/value                                                  |
+--------------------+----------+---------+----------------------------------------------------------------------------+
| state              | no       | present | 'absent' or 'present'                                                      |
+--------------------+----------+---------+----------------------------------------------------------------------------+

Example action from Ansible :doc:`playbooks`::

    apt_repository repo=ppa:nginx/stable
    apt_repository repo='deb http://archive.canonical.com/ubuntu hardy partner'
