.. _advanced_setup:

********************
Advanced Ansible setup
********************

With the introduction of collections, some content can be migrated in your own collection. This is especially useful when important content from multiple sources.

Also, as your ansible repo starts growing, you might not want to mix your inventories with your playbooks in the root folder.

.. contents::
   :local:

Advanced directory layout
-----------------------

With this setup, the root of your repo is quiet simple::

    inventories/
    collections/
    playbooks/
      tasks/
      files/
      templates/
    doc/ # Don't forget to fill this ;)
    vaults/
    ansible.cfg
    requirements.yml

To install and use collections from this folder, you need to update ``ansible.cfg`` with the following::

To and use collections from this folder, you need to update ``ansible.cfg`` with the following::

   [defaults]
   collections_paths = ./collections

To use a default hosts list, you can update ``ansible.cfg`` with the following configuration::

   [defaults]
   inventory = ./inventories/{{ default hosts list}}

.. note: You might notice that the folders ``roles``, ``library``, ``module_utils`` and ``filter_plugins`` are no longer present in this layout. This is because they should now be referenced exclusively from collections.

Organizing your inventory
-----------------------

First, remember to split your variables from your inventory sources (:ref:`splitting_out_vars`).

As in the traditional setup, there are still two ways to organize your inventories:: within a single folder or in multiple folders. Multiple folders are particularly useful if your ``group_vars``/``host_vars`` don't have that much in common in different environments.

Using a single inventory folder would look like this::

    inventories/
        production                # inventory file for production servers
        staging                   # inventory file for staging environment

        group_vars/
        host_vars/

Using a multiple inventory folders would look like this::

    inventories/
       production/
          hosts               # inventory file for production servers
          group_vars/
          host_vars/

       staging/
          hosts               # inventory file for staging environment
          group_vars/
          host_vars/


Absolute paths
--------------

Considering you might want to reorganize files referenced in your playbooks later, you should consider using absolute paths. To do that, set the following variables for the `all` group::

    ansible_repo_path: "{{ ansible_config_file[:-12] }}" # Get current repo path : remove trailing /ansible.cfg
    files_path: "{{ ansible_repo_path }}/playbooks/files"
    templates_path: "{{ ansible_repo_path }}/playbooks/templates"
    tasks_path: "{{ ansible_repo_path }}/playbooks/tasks"
    vaults_path: "{{ ansible_repo_path }}/playbooks/vaults"

Then, after creating the file ``playbooks/files/foo.conf``, you can reference it in your playbooks like this::

    - name: Copy file
      ansible.builtin.copy:
        src: {{ files_path }}/foo.conf
        dest: /etc/foo.conf

.. note: This use the fact that you have a ``ansible.cfg`` file at the root of your folder. If this file doesn't exists, this method won't work.


Organizing your playbooks
-------------------------

Once you start having a lot of playbooks and some reusable tasks, you might to organize them::

    playbooks/
      tools/ # Used to manipulate some hosts. Ex: ping, show_groups
      actions/ # For actions. Ex: update, sync, restart, ...
      provisionning/ # Run once provisionning playbooks. Ex: configure ssh, install python, ...
      hosts/ # For playbooks manipulating a single host
      service/ # Content related to a service manipulation. Ex: deploy monitoring on all hosts

.. note: There are various ways to organize playbooks, this is a first draft at how they could be organized

.. seealso::

   :ref:`sample_setup`
       See traditional setup
   `GitHub examples directory <https://github.com/ansible/ansible-examples>`_
       Complete playbook files from the github project source
   `Mailing List <https://groups.google.com/group/ansible-project>`_
       Questions? Help? Ideas?  Stop by the list on Google Groups
