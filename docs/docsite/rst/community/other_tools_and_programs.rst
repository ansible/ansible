########################
Other Tools And Programs
########################

.. contents:: Topics

The Ansible community provides several useful tools for working with the Ansible project. This is a list of some of the most popular of these tools.

If you know of any other tools that should be added, this list can be updated by clicking "Edit on GitHub" on the top right of this page.

*******
Editors
*******

Atom
====

Is a open source and free GUI text editor by GitHub. It can keep track of git project
changes, can commit from the GUI and see what branch you are on. You can customize the
themes for different colors and install packages to help with different languages Language
YAML. You can install it on Linux, OSX and Windows.

* `Language YAML <https://github.com/atom/language-yaml>`_


PyCharm
=======

Is a full IDE to develop Python software. It has all the needed parts to be able to write
python scripts and complete software. Is a little overkill for writing roles/playbooks but, it can
be a very useful tool if you write modules and submit code for Ansible. Can be used to debug the Ansible engine.

* Yaml supported out of the box


Sublime
=======

You can customize GUI with themes, install packages and do the same type of work. You can install it on
Linux, OSX and Windows

* `GitGutter <https://packagecontrol.io/packages/GitGutter>`_ - plug-in to show information about files in a git repository
* `SideBarEnhancements <https://packagecontrol.io/packages/SideBarEnhancements>`_ - Provides enhancements to the operations on Sidebar of Files and Folders
* `Sublime Linter <https://packagecontrol.io/packages/SublimeLinter>`_ - The code linting framework for Sublime Text 3
* `Pretty YAML <https://packagecontrol.io/packages/Pretty%20YAML>`_ - Prettify YAML plugin for Sublime Text 2 & 3
* `Yamllint <https://packagecontrol.io/packages/SublimeLinter-contrib-yamllint>`_ - Sublime wrapper around yamllint

VS Code
=======

Also similar like Atom & sublime but, made by Microsoft. Its also open source and free.


* `YAML Support by Red Hat <https://marketplace.visualstudio.com/items?itemName=redhat.vscode-yaml>`_ - Provides YAML support via yaml-language-server with built-in Kubernetes and Kedge syntax support.
* `Ansible Syntax Highlighting Extension <https://marketplace.visualstudio.com/items?itemName=haaaad.ansible>`_ - YAML & Jinja2 support
* `Visual Studio Code extension for Ansible <https://marketplace.visualstudio.com/items?itemName=vscoss.vscode-ansible>`_ - Autocompletion, syntax highlighting

vim
====

* `Ansible vim <https://github.com/pearofducks/ansible-vim>`_  - vim syntax plugin for Ansible 2.x, it supports YAML playbooks, Jinja2 templates, and Ansible's hosts files.


********************
Validating Playbooks
********************

- `Ansible Lint <https://github.com/willthames/ansible-lint>`_ is a widely used, highly configurable best-practices linter for Ansible playbooks.
- `Ansible Review <https://github.com/willthames/ansible-review>`_ is an extension of Ansible Lint designed for code review.
- `Molecule <http://github.com/metacloud/molecule>`_ A testing framework for Ansible plays and roles.

********
Run time
********

- `ARA Records Ansible <http://github.com/openstack/ara>`_ ARA Records Ansible playbook runs and makes the recorded data available and intuitive for users and systems.

*************
Visualization
*************

- `Ansible Inventory Grapher <http://github.com/willthames/ansible-inventory-grapher>`_ can be used to visually display inventory inheritance hierarchies and at what level a variable is defined in inventory.


******
Others
******

- `Ansigenome <https://github.com/nickjj/ansigenome>`_ is a command line tool designed to help you manage your Ansible roles.
- `Awesome Ansible <https://github.com/jdauphant/awesome-ansible>`_ is a collaboratively curated list of awesome Ansible resources.
- `Ansible cmdb` <https://github.com/fboender/ansible-cmdb`_ - Takes the output of Ansible's fact gathering and converts it into a static HTML overview page containing system configuration information
- `Ansible Shell` <https://github.com/dominis/ansible-shell`_ - Interactive shell for Ansible with built-in tab completion for all the modules
- `Ansible Silo` <https://github.com/groupon/ansible-silo`_ - Ansible in a self-contained environment via Docker.
- `AWX` <https://github.com/ansible/awx`_ - AWX provides a web-based user interface, REST API, and task engine built on top of Ansible. It is the upstream project for Tower, a commercial derivative of AWX.
- `Mitogen for Ansible` <https://mitogen.readthedocs.io/en/latest/ansible.html`_ - Uses the `Mitogen <https://github.com/dw/mitogen/>`_ library to execute Ansible playbooks in a more efficient way (decreases the execution time).
- `OpsTools-ansible` <https://github.com/centos-opstools/opstools-ansible`_ - The project opstools-ansible is to use Ansible to configure an environment that provides the support of `OpsTools` <https://wiki.centos.org/SpecialInterestGroup/OpsTools>, namely centralized logging and analysis, availability monitoring, and performance monitoring.
- `TD4A` <https://github.com/cidrblock/td4a`_ - Template designer for automation - TD4A is a visual design aid for building and testing jinja2 templates. It will combine data in yaml format with a jinja2 template and render the output.


*****************
Development Tools
*****************

Finding related issues and PRs
==============================

There are various ways to find existing issues and pull request (PRs)


- `PR by File <https://ansible.sivel.net/pr/byfile.html>`_ shows a current list of all open pull requests by individual file. An essential tool for Ansible module maintainers.
- `jctanner's Ansible Tools <https://github.com/jctanner/ansible-tools>`_ is a miscellaneous collection of useful helper scripts for Ansible development.

