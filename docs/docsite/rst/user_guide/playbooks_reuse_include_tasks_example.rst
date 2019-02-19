Include_tasks: A Worked Example
===============================

As described on the previous page, the include_tasks module enables the user to break a playbook into smaller, more manageable files that can be reused when required in plays, playbooks and roles. It is the very essence of good coding:

1) Break up large programs into smaller blocks
2) Reuse those blocks, without reinventing the wheel, as many times as required

The include_tasks module is used as follows::

        - name: [task name]
          include_tasks: [list of tasks.yml]

This document shows *how* the include_tasks module could be used: starting with a playbook, breaking the playbook into separate files, and then assembling a new playbook out of the new files.

The Initial Playbook
````````````````````
Below is an example of a large, unwieldy playbook. It updates the computer, installs repos, installs some software and uninstalls some other software::

        # original_playbook.yml
        # building a RHEL desktop
        - hosts: all
          remote_user: ansible
          tasks:
          - name: update server
            yum:
              name: '*'
              state: latest
        - name: add epel-release
          yum:
            name: epel-release
            state: present
        - name: add rpmfusion
          yum:
            name: https://download1.rpmfusion.org/free/el/rpmfusion-free-release-7.noarch.rpm
            state: present
        - name: install RHEL software
          yum:
            name: '{{ packages }}'
            state: present
          vars:
            packages:
              - hamster-time-tracker
              - kate
              - Zim
              - vlc
              - htop
              - atop
              - okular
              - gcc
        - name: remove RHEL software
          yum:
            name: '{{ packages }}'
            state: absent
          vars:
            packages:
              - neovim
              - gnome-weather
              - orca
              - evince
              - mg
              - nano
              - pico
              - gnome-boxes

Dismantling The Initial Playbook
````````````````````````````````
Original_playbook.yml is not overly large, but given time, it could get big and ugly. Let's break it down into task files. Each task file below, represents one of the actions that original_playbook.yml performed - update server, install repos, install software and remove software. The task files are named as such:

- update_my_box.yml - a task file for updating a server
- install_github_repos.yml - a task file for installing Github repositories
- install_RHEL_software.yml - a task file for installing some useful desktop software
- remove_RHEL_software.yml - a task file for removing software that is no longer needed

Their contents are below::

        ---
        # update_my_box.yml
        - name: update server
          yum:
            name: '*'
            state: latest

        ---
        # install_github_repos.yml
        - name: add epel-release
          yum:
            name: epel-release
            state: present
        - name: add rpmfusion
          yum:
            name: https://download1.rpmfusion.org/free/el/rpmfusion-free-release-7.noarch.rpm
            state: present

        ---
        # install_RHEL_software.yml
        - name: install RHEL software
          yum:
            name: '{{ packages }}'
            state: present
          vars:
            packages:
              - hamster-time-tracker
              - kate
              - Zim
              - vlc
              - htop
              - atop
              - okular
              - gcc

        ---
        # remove_RHEL_software.yml
        - name: remove RHEL software
          yum:
            name: '{{ packages }}'
            state: absent
          vars:
            packages:
              - neovim
              - gnome-weather
              - orca
              - evince
              - mg
              - nano
              - pico
              - gnome-boxes

Recreating The New Playbook
```````````````````````````
The file Original_playbook.yml has been split into four small, (reusable), task books. The include_tasks module can be used to create a new playbook (named RHEL_desktop.yml) that calls those task books, as shown below:: 

        ---
        # RHEL_desktop.yml
        # building a RHEL desktop
        - hosts: all
          remote_user: root
          tasks:
          - name: update my box
            include_tasks: /home/redfern/ansible/playbooks/update_my_box.yml
          - name: install github repositories
            include_tasks: /home/redfern/ansible/playbooks/install_github_repos.yml
          - name: install RHEL software
            include_tasks: /home/redfern/ansible/playbooks/install_RHEL_software.yml
          - name: remove RHEL software
            include_tasks: /home/redfern/ansible/playbooks/remove_RHEL_software.yml

On Headers
``````````
Playbooks (e.g. RHEL_desktop.yml, above) have file headers composed of the affected hosts, the user that will perform the tasks and the task section (the included tasks from earlier). Task files *don't*. This means that in order to run your task file, you need a playbook to do it. The playbook provides the information Ansible needs to perform the tasks you tell it.



