Getting Started with Ansible in a Self-Contained Project Structure
==================================================================

Introduction
------------
This guide will walk you through setting up a self-contained project structure for working with Ansible. The goal is to create a single directory that can easily be committed to a GitHub repository and used with tools like AWX and Navigator. Additionally, we will integrate Visual Studio Code (VSCode) and Ansible Lint for an improved development experience.

Step 1: Create a Project Directory
----------------------------------
Start by creating a new directory in your home directory. This will serve as the root directory for your Ansible project.

.. code-block:: shell

   $ mkdir ansible-project
   $ cd ansible-project

Step 2: Set up the Inventory
---------------------------
Next, let's create the inventory file for your Ansible project. This file will contain the list of hosts or groups of hosts that Ansible will manage. Create a file named ``inventory`` in the project directory.

.. code-block:: shell

   $ touch inventory

You can now add the necessary hosts and groups to the ``inventory`` file using your preferred text editor. Make sure to follow the correct INI file format.

Step 3: Organize Playbooks
--------------------------
Now, let's create a directory to store your Ansible playbooks and place them adjacent to the inventory file. This will keep all your playbooks in one place, making it easier to manage and version control.

.. code-block:: shell

   $ mkdir playbooks

You can now start adding your Ansible playbooks to the ``playbooks`` directory. For example, you could create a playbook named ``setup.yml``:

.. code-block:: shell

   $ touch playbooks/setup.yml

Step 4: Manage Collections
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
By following this guide, you have successfully set up a self-contained Ansible project structure. Your project directory now includes an organized inventory file, playbooks directory, and collections directory. This structure allows for easy management, version control, and integration with tools like AWX and Navigator.

Additionally, you have configured Visual Studio Code (VSCode) as your development environment and incorporated Ansible Lint for an improved development experience. With syntax highlighting, linting, and other features provided by VSCode, you can write and manage your Ansible code more efficiently.

You are now ready to commit your project to a GitHub repository or any other version control system of your choice. Enjoy working on your Ansible projects with this streamlined and self-contained project structure!