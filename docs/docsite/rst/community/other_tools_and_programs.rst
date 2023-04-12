.. _other_tools_and_programs:

************************
Other Tools and Programs
************************

.. contents::
   :local:

The Ansible community uses a range of tools for working with the Ansible project. This is a list of some of the most popular of these tools.

If you know of any other tools that should be added, this list can be updated by clicking "Edit on GitHub" on the top right of this page.


Popular editors
===============


Emacs
-----

A free, open-source text editor and IDE that supports auto-indentation, syntax highlighting and built in terminal shell(among other things).

* `yaml-mode <https://github.com/yoshiki/yaml-mode>`_ - YAML highlighting and syntax checking.
* `jinja2-mode <https://github.com/paradoxxxzero/jinja2-mode>`_ - Jinja2 highlighting and syntax checking.
* `magit-mode <https://github.com/magit/magit>`_ -  Git porcelain within Emacs.
* `lsp-mode <https://emacs-lsp.github.io/lsp-mode/page/lsp-ansible/>`_ - Ansible syntax highlighting, auto-completion and diagnostics.


PyCharm
-------

A full IDE (integrated development environment) for Python software development. It ships with everything you need to write python scripts and complete software, including support for YAML syntax highlighting. It's a little overkill for writing roles/playbooks, but it can be a very useful tool if you write modules and submit code for Ansible. Can be used to debug the Ansible engine. For more information, see `PyCharm <https://www.jetbrains.com/pycharm/>`_


Sublime
-------

A closed-source, subscription GUI text editor. You can customize the GUI with themes and install packages for language highlighting and other refinements. You can install Sublime on Linux, macOS and Windows. Useful Sublime plugins include:

* `GitGutter <https://packagecontrol.io/packages/GitGutter>`_ - shows information about files in a git repository.
* `SideBarEnhancements <https://packagecontrol.io/packages/SideBarEnhancements>`_ - provides enhancements to the operations on Sidebar of Files and Folders.
* `Sublime Linter <https://packagecontrol.io/packages/SublimeLinter>`_ - a code-linting framework for Sublime Text 3.
* `Pretty YAML <https://packagecontrol.io/packages/Pretty%20YAML>`_ - prettifies YAML for Sublime Text 2 and 3.
* `Yamllint <https://packagecontrol.io/packages/SublimeLinter-contrib-yamllint>`_ - a Sublime wrapper around yamllint.


vim
---

An open-source, free command-line text editor. Useful vim plugins include:

* `Ansible vim <https://github.com/pearofducks/ansible-vim>`_  - vim syntax plugin for Ansible 2.x, it supports YAML playbooks, Jinja2 templates, and Ansible's hosts files.
* `Ansible vim and neovim plugin <https://www.npmjs.com/package/@yaegassy/coc-ansible>`_  - vim plugin (lsp client) for Ansible, it supports autocompletion, syntax highlighting, hover, diagnostics, and goto support.


Visual studio code
------------------

An open-source, free GUI text editor created and maintained by Microsoft. Useful Visual Studio Code plugins include:

* `Ansible extension by Red Hat <https://marketplace.visualstudio.com/items?itemName=redhat.ansible>`_ - provides autocompletion, syntax highlighting, hover, diagnostics, goto support, and command to run ansible-playbook and ansible-navigator tool for both local and execution-environment setups.
* `YAML Support by Red Hat <https://marketplace.visualstudio.com/items?itemName=redhat.vscode-yaml>`_ - provides YAML support through yaml-language-server with built-in Kubernetes and Kedge syntax support.


.. note::

    Visual studio code is not maintained by the community.




Development tools
=================

Finding related issues and PRs
------------------------------

There are various ways to find existing issues and pull requests (PRs)

- `jctanner's Ansible Tools <https://github.com/jctanner/ansible-tools>`_ - miscellaneous collection of useful helper scripts for Ansible development.

.. _validate-playbook-tools:


Tools for validating playbooks
==============================

- `Ansible Lint <https://docs.ansible.com/ansible-lint/index.html>`_ - a highly configurable linter for Ansible playbooks.
- `Ansible Review <https://github.com/willthames/ansible-review>`_ - an extension of Ansible Lint designed for code review.
- `Molecule <https://molecule.readthedocs.io/en/latest/>`_ - a testing framework for Ansible plays and roles.
- `yamllint <https://yamllint.readthedocs.io/en/stable/>`__ - a command-line utility to check syntax validity including key repetition and indentation issues.



Other tools
===========

- `Ansible cmdb <https://github.com/fboender/ansible-cmdb>`_ - takes the output of Ansible's fact gathering and converts it into a static HTML overview page containing system configuration information.
- `Ansible Inventory Grapher <https://github.com/willthames/ansible-inventory-grapher>`_ - visually displays inventory inheritance hierarchies and at what level a variable is defined in inventory.
- `Ansible Language Server <https://www.npmjs.com/package/@ansible/ansible-language-server>`_ - a server that implements `language server protocol <https://microsoft.github.io/language-server-protocol/>`_ for Ansible.
- `Ansible Playbook Grapher <https://github.com/haidaraM/ansible-playbook-grapher>`_ - a command line tool to create a graph representing your Ansible playbook tasks and roles.
- `Ansible Shell <https://github.com/dominis/ansible-shell>`_ - an interactive shell for Ansible with built-in tab completion for all the modules.
- `Ansible Silo <https://github.com/groupon/ansible-silo>`_ - a self-contained Ansible environment by Docker.
- `Ansigenome <https://github.com/nickjj/ansigenome>`_ - a command line tool designed to help you manage your Ansible roles.
- `antsibull-changelog <https://github.com/ansible-community/antsibull-changelog>`_ - a changelog generator for Ansible collections.
- `antsibull-docs <https://github.com/ansible-community/antsibull-docs>`_ - generates docsites for collections and can validate collection documentation.
- `ARA <https://github.com/ansible-community/ara>`_ - ARA Records Ansible playbooks and makes them easier to understand and troubleshoot with a reporting API, UI and CLI.
- `Awesome Ansible <https://github.com/ansible-community/awesome-ansible>`_ - a collaboratively curated list of awesome Ansible resources.
- `AWX <https://github.com/ansible/awx>`_ - provides a web-based user interface, REST API, and task engine built on top of Ansible. Red Hat Ansible Automation Platform includes code from AWX.
- `Mitogen for Ansible <https://mitogen.networkgenomics.com/ansible_detailed.html>`_ - uses the `Mitogen <https://github.com/dw/mitogen/>`_ library to execute Ansible playbooks in a more efficient way (decreases the execution time).
- `nanvault <https://github.com/marcobellaccini/nanvault>`_ - a standalone tool to encrypt and decrypt files in the Ansible Vault format, featuring UNIX-style composability.
- `OpsTools-ansible <https://github.com/centos-opstools/opstools-ansible>`_ - uses Ansible to configure an environment that provides the support of `OpsTools <https://wiki.centos.org/SpecialInterestGroup/OpsTools>`_, namely centralized logging and analysis, availability monitoring, and performance monitoring.
- `Steampunk Spotter <https://pypi.org/project/steampunk-spotter/>`_ - provides an Assisted Automation Writing tool that analyzes and offers recommendations for your Ansible Playbooks.
- `TD4A <https://github.com/cidrblock/td4a>`_ - a template designer for automation. TD4A is a visual design aid for building and testing jinja2 templates. It will combine data in yaml format with a jinja2 template and render the output.
- `PHP-Ansible <https://github.com/maschmann/php-ansible>`_ - an object oriented Ansible wrapper for PHP.
