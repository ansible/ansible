Getting Started with Ansible in a Self-Contained Project Structure
==================================================================

Introduction to Ansible
-----------------------

Ansible is an open-source automation platform that allows IT professionals to automate various areas of their domain, for example:

* repetitive tasks
* system configuration
* software deployments
* continuous deployments
* zero downtime rolling updates

Users can write simple, human-readable automation scripts called playbooks. Those playbooks utilize a declarative approach to describe the desired state of a remote or local system (a managed host) that Ansible should ensure.

Ansible is decentralized is a sense that it relies on your existing OS credentials to control access to remote machines. And if needed, Ansible can easily connect with Kerberos, LDAP, and other centralized authentication management systems.

The following are some of the key strengths of Ansible:

* agent-less architecture: no need for agents or additional software to be installed on managed hosts. This reduces maintenance overhead.

* simplicity: Ansible features a minimum of moving parts, uses YAML syntax for its playbooks and leverages SSH/WinRM protocols to establish secure connections to execute tasks remotely.

* scalability and flexibility: modular design enables users to quickly and easily scale from one managed host to many. Support for wide range of operating systems, cloud platforms and network devices make Ansible also a very flexible automation platform.

* idempotence and predictability: when the managed host is in the correct state, running the same playbook multiple times does no changes.

Ansible releases a new major release approximately twice a year. The core application (`ansible-core`) evolves somewhat conservatively, valuing simplicity in language design and setup. Contributors develop and change modules and plugins hosted in collections since version 2.10 more quickly.


.. note::

   This documentation covers the version of Ansible noted in the upper left corner of this page. The community maintains multiple versions of Ansible and of the documentation. Be sure you use the documentation that matches the version of software that you need. For recent features, we note the time of addition.


Setting up Ansible project
--------------------------
This guide will walk you through setting up a self-contained project structure for working with Ansible. The goal is to create a single directory that can easily be committed to a GitHub repository and used with utilities like AWX and Navigator. Additionally, we will integrate Visual Studio Code (VSCode) and Ansible Lint for an improved development experience.

Step 1: Create a project directory
----------------------------------
Start by creating a new directory in your home directory. This will serve as the root directory for your Ansible project.

.. code-block:: shell

   $ mkdir ansible-project
   $ cd ansible-project

Step 2: Create the host inventory
---------------------------------
Next, let's create the inventory file for your Ansible project. This file will contain the list of hosts or groups of hosts that Ansible will manage. Create a file named ``inventory`` in the project directory.

.. code-block:: shell

   $ touch inventory

You can now add the necessary hosts and groups to the ``inventory`` file using your preferred text editor. Make sure to follow the correct INI file format.

Step 3: Organize playbooks
--------------------------
Now, let's create a directory to store your Ansible playbooks and place them adjacent to the inventory file. This will keep all your playbooks in one place, making it easier to manage and version control.

.. code-block:: shell

   $ mkdir playbooks

You can now start adding your Ansible playbooks to the ``playbooks`` directory. For example, you could create a playbook named ``setup.yml``:

.. code-block:: shell

   $ touch playbooks/setup.yml

Step 4: Manage collections
--------------------------
To manage Ansible collections used in your project, create a directory called ``collections`` within the project directory.

.. code-block:: shell

   $ mkdir collections

You can now add the necessary collections to a ``requirements.yml`` file inside the ``collections`` directory. This file will serve as a manifest for the collections your project depends on.

.. code-block:: shell

   $ touch collections/requirements.yml

Inside the ``requirements.yml`` file, list the collections you need, specifying the name and version. For example:

.. code-block:: yaml

   ---
   collections:
     - name: ansible.posix
       version: 1.3.0
     - name: community.general
       version: 3.8.0

Step 5: Configure VSCode and Lint
---------------------------------
To enhance your development experience, we will set up Visual Studio Code (VSCode) as your development environment and incorporate linting for Ansible.

1. Install the "Ansible" extension for VSCode.
2. Open the project directory in VSCode: ``$ code .``
3. Install the "ansible-lint" Python package globally or in a virtual environment: ``$ pip install ansible-lint``

VSCode should now provide syntax highlighting, linting, and other useful features for Ansible development.

Step 6: Commit to GitHub
------------------------
You now have a self-contained Ansible project structure that can be easily committed to a GitHub repository. Initialize a new Git repository and add all the files:

.. code-block:: shell

   $ git init
   $ git add .
   $ git commit -m "Initial commit"

You can now push your project to GitHub or any other version control system of your choice.

Conclusion
----------
By following this guide, you have successfully set up a self-contained Ansible project structure. Your project directory now includes an organized inventory file, playbooks directory, and collections directory. This structure allows for easy management, version control, and integration with utilities like AWX and Navigator.

Additionally, you have configured Visual Studio Code (VSCode) as your development environment and incorporated Ansible Lint for an improved development experience. With syntax highlighting, linting, and other features provided by VSCode, you can write and manage your Ansible code more efficiently.

You are now ready to commit your project to a GitHub repository or any other version control system of your choice. Enjoy working on your Ansible projects with this streamlined and self-contained project structure!