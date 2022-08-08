.. _installation_guide:
.. _intro_installation_guide:

******************
Installing Ansible
******************

Ansible is an agentless automation tool that you install on a single host (referred to as the control node). From the control node, Ansible can manage an entire fleet of machines and other devices (referred to as managed nodes) remotely with SSH, Powershell remoting, and numerous other transports, all from a simple command-line interface with no databases or daemons required.

.. contents::
  :local:

.. _control_node_requirements:

Control node requirements
=========================

For your *control* node (the machine that runs Ansible), you can use nearly any UNIX-like machine with Python 3.9 or newer installed. This includes Red Hat, Debian, Ubuntu, macOS, BSDs, and Windows under a `Windows Subsystem for Linux (WSL) distribution <https://docs.microsoft.com/en-us/windows/wsl/about>`_. Windows without WSL is not natively supported as a control node; see `Matt Davis' blog post <http://blog.rolpdog.com/2020/03/why-no-ansible-controller-for-windows.html>`_ for more information.

.. _managed_node_requirements:

Managed node requirements
=========================

The *managed* node (the machine that Ansible is managing) does not require Ansible to be installed, but requires Python 2.7, or Python 3.5 - 3.11 to run Ansible library code.

.. note::

   Network modules are an exception and do not require Python on the managed device.  See :ref:`network_modules`.

.. _node_requirements_summary:

Node requirement summary
========================

The table below lists the current and historical versions of Python
required on control and managed nodes.

.. list-table::
   :header-rows: 1

   * - ansible-core Version
     - Control node Python
     - Managed node Python
   * - 2.11
     - Python 2.7, Python 3.5 - 3.9 `[†]`_
     - Python 2.6 - 2.7, Python 3.5 - 3.9
   * - 2.12
     - Python 3.8 - 3.10
     - Python 2.6 - 2.7, Python 3.5 - 3.10
   * - 2.13
     - Python 3.8 - 3.10
     - Python 2.7, Python 3.5 - 3.10
   * - 2.14
     - Python 3.9 - 3.11
     - Python 2.7, Python 3.5 - 3.11

_`[†]`: Has a soft requirement of Python 3.8 as not packaged for older versions

.. _getting_ansible:

.. _what_version:

Selecting an Ansible package and version to install
====================================================

Ansible's community packages are distributed in two ways: a minimalist language and runtime package called ``ansible-core``, and a much larger "batteries included" package called ``ansible``, which adds a community-curated selection of :ref:`Ansible Collections <collections>` for automating a wide variety of devices. Choose the package that fits your needs; The following instructions  use ``ansible``, but  you can substitute ``ansible-core``  if you prefer to start with a more minimal package and separately install only the Ansible Collections you require. The ``ansible`` or ``ansible-core`` packages may be available in your operating systems package manager, and you are free to install these packages with your preferred method. These installation instructions only cover the officially supported means of installing the python package with ``pip``.

Installing and upgrading Ansible
================================

Locating Python
---------------

Locate and remember the path to the Python interpreter you wish to use to run Ansible. The following instructions refer to this Python  as ``python3``. For example, if you've determined that you want the Python at ``/usr/bin/python3.9`` to be the one that you'll install Ansible under, specify that instead of ``python3``.

Ensuring ``pip`` is available
-----------------------------

To verify whether ``pip`` is already installed for your preferred Python:

.. code-block:: console

    $ python3 -m pip -V

If all is well, you should see something like the following:

.. code-block:: console

    $ python3 -m pip -V
    pip 21.0.1 from /usr/lib/python3.9/site-packages/pip (python 3.9)

If so, ``pip`` is available, and you can move on to the :ref:`next step <pip_install>`.

If you see an error like ``No module named pip``, you'll need to install ``pip`` under your chosen Python interpreter before proceeding. This may mean installing an additional OS package (for example, ``python3-pip``), or installing the latest ``pip`` directly from the Python Packaging Authority by running the following:

.. code-block:: console

    $ curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
    $ python3 get-pip.py --user

You may need to perform some additional configuration before you are able to run Ansible. See the Python documentation on `installing to the user site`_ for more information.

.. _installing to the user site: https://packaging.python.org/tutorials/installing-packages/#installing-to-the-user-site

.. _pip_install:

Installing Ansible
------------------

Use ``pip`` in your selected Python environment to install the Ansible package of your choice for the current user:

.. code-block:: console

    $ python3 -m pip install --user ansible

Alternately, you can install a specific version of ``ansible-core`` in this Python environment:

.. code-block:: console

    $ python3 -m pip install --user ansible-core==2.12.3

.. _pip_upgrade:

Upgrading Ansible
-----------------

To upgrade an existing Ansible installation in this Python environment to the latest released version, simply add ``--upgrade`` to the command above:

.. code-block:: console

    $ python3 -m pip install --upgrade --user ansible

Confirming your installation
----------------------------

You can test that Ansible is installed correctly by checking the version:

.. code-block:: console

    $ ansible --version

The version displayed by this command is for the associated ``ansible-core`` package that has been installed.

To check the version of the ``ansible`` package that has been installed:

.. code-block:: console

    $ python3 -m pip show ansible

.. _development_install:

Installing for development
==========================

If you are testing new features, fixing bugs, or otherwise working with the development team on changes to the core code, you can install and run the source from GitHub.

.. note::

    You should only install and run the ``devel`` branch if you are modifying ``ansible-core`` or trying out features under development. This is a rapidly changing source of code and can become unstable at any point.

For more information on getting involved in the Ansible project, see the :ref:`ansible_community_guide`. For more information on creating Ansible modules and Collections, see the :ref:`developer_guide`.

.. _from_pip_devel:

Installing ``devel`` from GitHub with ``pip``
---------------------------------------------

You can install the ``devel`` branch of ``ansible-core`` directly from GitHub with ``pip``:

.. code-block:: console

    $ python3 -m pip install --user https://github.com/ansible/ansible/archive/devel.tar.gz

You can replace ``devel`` in the URL mentioned above, with any other branch or tag on GitHub to install older versions of Ansible, tagged alpha or beta versions, and release candidates.

.. _from_source:

Running the ``devel`` branch from a clone
-----------------------------------------

``ansible-core`` is easy to run from source. You do not need ``root`` permissions to use it and there is no software to actually install. No daemons or database setup are required.

#. Clone the ``ansible-core`` repository

   .. code-block:: console

      $ git clone https://github.com/ansible/ansible.git
      $ cd ./ansible

#. Setup the Ansible environment

   * Using Bash

     .. code-block:: console

        $ source ./hacking/env-setup

   * Using Fish

     .. code-block:: console

        $ source ./hacking/env-setup.fish

   * To suppress spurious warnings/errors, use ``-q``

     .. code-block:: console

        $ source ./hacking/env-setup -q

#. Install Python dependencies

   .. code-block:: console

      $ python3 -m pip install --user -r ./requirements.txt

#. Update the ``devel`` branch of ``ansible-core`` on your local machine

   Use pull-with-rebase so any local changes are replayed.

   .. code-block:: console

      $ git pull --rebase

.. _shell_completion:

Adding Ansible command shell completion
=======================================

You can add shell completion of the Ansible command line utilities by installing an optional dependency called ``argcomplete``. ``argcomplete`` supports bash, and has limited support for zsh and tcsh.

For more information about installation and configuration, see the `argcomplete documentation <https://kislyuk.github.io/argcomplete/>`_.

Installing ``argcomplete``
--------------------------

.. code-block:: console

    $ python3 -m pip install --user argcomplete

Configuring ``argcomplete``
---------------------------

There are 2 ways to configure ``argcomplete`` to allow shell completion of the Ansible command line utilities: globally or per command.

Global configuration
^^^^^^^^^^^^^^^^^^^^

Global completion requires bash 4.2.

.. code-block:: console

    $ activate-global-python-argcomplete

This will write a bash completion file to a global location. Use ``--dest`` to change the location.

Per command configuration
^^^^^^^^^^^^^^^^^^^^^^^^^

If you do not have bash 4.2, you must register each script independently.

.. code-block:: console

    $ eval $(register-python-argcomplete ansible)
    $ eval $(register-python-argcomplete ansible-config)
    $ eval $(register-python-argcomplete ansible-console)
    $ eval $(register-python-argcomplete ansible-doc)
    $ eval $(register-python-argcomplete ansible-galaxy)
    $ eval $(register-python-argcomplete ansible-inventory)
    $ eval $(register-python-argcomplete ansible-playbook)
    $ eval $(register-python-argcomplete ansible-pull)
    $ eval $(register-python-argcomplete ansible-vault)

You should place the above commands into your shells profile file such as ``~/.profile`` or ``~/.bash_profile``.

Using ``argcomplete`` with zsh or tcsh
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

See the `argcomplete documentation <https://kislyuk.github.io/argcomplete/>`_.


.. seealso::

   :ref:`intro_adhoc`
       Examples of basic commands
   :ref:`working_with_playbooks`
       Learning ansible's configuration management language
   :ref:`installation_faqs`
       Ansible Installation related to FAQs
   `Mailing List <https://groups.google.com/group/ansible-project>`_
       Questions? Help? Ideas?  Stop by the list on Google Groups
   :ref:`communication_irc`
       How to join Ansible chat channels
