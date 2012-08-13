.. _apt:

apt
```

Manages apt-packages (such as for Debian/Ubuntu).

+--------------------+----------+---------+----------------------------------------------------------------------------+
| parameter          | required | default | comments                                                                   |
+====================+==========+=========+============================================================================+
| name               | no       |         | A package name or package specifier with version, like `foo` or `foo=1.0`  |
+--------------------+----------+---------+----------------------------------------------------------------------------+
| state              | no       | present | 'absent', 'present', or 'latest'.                                          |
+--------------------+----------+---------+----------------------------------------------------------------------------+
| update_cache       | no       | no      | Run the equivalent of apt-get update before the operation.                 |
|                    |          |         | Can be run as part of the package installation or a seperate step          |
+--------------------+----------+---------+----------------------------------------------------------------------------+
| purge              | no       | no      | Will forge purge of configuration files if state is set to 'absent'.       |
+--------------------+----------+---------+----------------------------------------------------------------------------+
| default_release    | no       |         | Corresponds to the -t option for apt and sets pin priorities               |
+--------------------+----------+---------+----------------------------------------------------------------------------+
| install_recommends | no       | yes     | Corresponds to the --no-install-recommends option for apt, default         |
|                    |          |         | behavior works as apt's default behavior, 'no' does not install            |
|                    |          |         | recommended packages.  Suggested packages are never installed.             |
+--------------------+----------+---------+----------------------------------------------------------------------------+
| force              | no       | no      | If 'yes', force installs/removes.                                          |
+--------------------+----------+---------+----------------------------------------------------------------------------+

Example action from Ansible :doc:`playbooks`::

    apt pkg=foo update-cache=yes
    apt pkg=foo state=removed
    apt pkg=foo state=installed
    apt pkg=foo=1.00 state=installed
    apt pkg=nginx state=latest default-release=squeeze-backports update-cache=yes
    apt pkg=openjdk-6-jdk state=latest install-recommends=no
