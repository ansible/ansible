.. _installing_the_control_node:
.. _from_yum:

Installing Ansible on specific operating systems
================================================

Follow these instructions to install the Ansible community package on a variety of operating systems.

Installing Ansible on CentOS or Fedora
----------------------------------------------

On Fedora:

.. code-block:: bash

    $ sudo dnf install ansible

On CentOS:

.. code-block:: bash

    $ sudo yum install epel-release
    $ sudo yum install ansible

RPMs for currently supported versions of CentOS are also available from `EPEL <https://fedoraproject.org/wiki/EPEL>`_.

Ansible can manage older operating systems that contain Python 2.6 or higher.

.. _from_apt:

Installing Ansible on Ubuntu
----------------------------

Ubuntu builds are available `in a PPA here <https://launchpad.net/~ansible/+archive/ubuntu/ansible>`_.

To configure the PPA on your machine and install Ansible run these commands:

.. code-block:: bash

    $ sudo apt update
    $ sudo apt install software-properties-common
    $ sudo add-apt-repository --yes --update ppa:ansible/ansible
    $ sudo apt install ansible

.. note:: On older Ubuntu distributions, "software-properties-common" is called "python-software-properties". You may want to use ``apt-get`` instead of ``apt`` in older versions. Also, be aware that only newer distributions (in other words, 18.04, 18.10, and so on) have a ``-u`` or ``--update`` flag, so adjust your script accordingly.

Debian/Ubuntu packages can also be built from the source checkout, run:

.. code-block:: bash

    $ make deb

Installing Ansible on Debian
----------------------------

Debian users may use the same source as the Ubuntu PPA (using the following table).

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
  * - Debian 9 (Stretch)
    - ->
    - Ubuntu 16.04 (Xenial)
  * - Debian 8 (Jessie)
    - ->
    - Ubuntu 14.04 (Trusty)

.. note::

    As of Ansible 4.0.0, new releases will only be generated for Ubuntu 18.04 (Bionic) or later releases.

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

See :ref:`windows_faq_ansible`

.. seealso::

    `Installing Ansible on ARch Linux <https://wiki.archlinux.org/title/Ansible#Installation>`_
       Distro-specific installation on Arch Linux
    `Installing Ansible on Clear Linux <https://clearlinux.org/software/bundle/ansible>`_
       Distro-specific installation on Clear Linux
