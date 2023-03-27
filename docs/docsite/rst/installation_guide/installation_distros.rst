.. _installing_distros:

Installing Ansible on specific operating systems
================================================

The ``ansible`` package can always be :ref:`installed from PyPI using pip <intro_installation_guide>` on most systems but it is also packaged and maintained by the community for a variety of Linux distributions.

The following instructions will guide you through installing the ``ansible`` package with your preferred distribution's package manager.

.. contents::
  :local:

Installing Ansible on Fedora or CentOS 
--------------------------------------

On Fedora:

.. code-block:: bash

    $ sudo dnf install ansible

On CentOS:

.. code-block:: bash

    $ sudo yum install epel-release
    $ sudo yum install ansible

RPMs for currently supported versions of CentOS are also available from `EPEL <https://fedoraproject.org/wiki/EPEL>`_.

Installing Ansible on OpenSUSE Tumbleweed/Leap
----------------------------------------------

.. code-block:: bash

    $ sudo zypper install ansible

.. _from_apt:

Installing Ansible on Ubuntu
----------------------------

Ubuntu builds are available `in a PPA here <https://launchpad.net/~ansible/+archive/ubuntu/ansible>`_.

To configure the PPA on your system and install Ansible run these commands:

.. code-block:: bash

    $ sudo apt update
    $ sudo apt install software-properties-common
    $ sudo add-apt-repository --yes --update ppa:ansible/ansible
    $ sudo apt install ansible

.. note:: On older Ubuntu distributions, "software-properties-common" is called "python-software-properties". You may want to use ``apt-get`` rather than ``apt`` in older versions. Also, be aware that only newer distributions (that is, 18.04, 18.10, and later) have a ``-u`` or ``--update`` flag. Adjust your script as needed.




Installing Ansible on Debian
----------------------------

Debian users can use the same source as the Ubuntu PPA (using the following table).

.. list-table::
  :header-rows: 1

  * - Debian
    -
    - Ubuntu
  * - Debian 11 (Bullseye)
    - ->
    - Ubuntu 20.04 (Focal)
  * - Debian 10 (Buster)
    - ->
    - Ubuntu 18.04 (Bionic)


.. note::

    Ansible releases are only built for Ubuntu 18.04 (Bionic) or later releases.

Add the following line to ``/etc/apt/sources.list`` or ``/etc/apt/sources.list.d/ansible.list``:

.. code-block:: bash

    deb http://ppa.launchpad.net/ansible/ansible/ubuntu MATCHING_UBUNTU_CODENAME_HERE main

Example for Debian 11 (Bullseye)

.. code-block:: bash

    deb http://ppa.launchpad.net/ansible/ansible/ubuntu focal main

Then run these commands:

.. code-block:: bash

    $ sudo apt-key adv --keyserver keyserver.ubuntu.com --recv-keys 93C4A3FD7BB9C367
    $ sudo apt update
    $ sudo apt install ansible



.. _from_windows:

Installing Ansible on Windows
------------------------------

You cannot use a Windows system for the Ansible control node. See :ref:`windows_faq_ansible`

.. seealso::

    `Installing Ansible on Arch Linux <https://wiki.archlinux.org/title/Ansible#Installation>`_
       Distro-specific installation on Arch Linux
    `Installing Ansible on Clear Linux <https://clearlinux.org/software/bundle/ansible>`_
       Distro-specific installation on Clear Linux
