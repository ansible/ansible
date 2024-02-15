[![PyPI version](https://img.shields.io/pypi/v/ansible-core.svg)](https://pypi.org/project/ansible-core)
[![Docs badge](https://img.shields.io/badge/docs-latest-brightgreen.svg)](https://docs.ansible.com/ansible/latest/)
[![Chat badge](https://img.shields.io/badge/chat-IRC-brightgreen.svg)](https://docs.ansible.com/ansible/latest/community/communication.html)
[![Build Status](https://dev.azure.com/ansible/ansible/_apis/build/status/CI?branchName=devel)](https://dev.azure.com/ansible/ansible/_build/latest?definitionId=20&branchName=devel)
[![Ansible Code of Conduct](https://img.shields.io/badge/code%20of%20conduct-Ansible-silver.svg)](https://docs.ansible.com/ansible/latest/community/code_of_conduct.html)
[![Ansible mailing lists](https://img.shields.io/badge/mailing%20lists-Ansible-orange.svg)](https://docs.ansible.com/ansible/latest/community/communication.html#mailing-list-information)
[![Repository License](https://img.shields.io/badge/license-GPL%20v3.0-brightgreen.svg)](COPYING)
[![Ansible CII Best Practices certification](https://bestpractices.coreinfrastructure.org/projects/2372/badge)](https://bestpractices.coreinfrastructure.org/projects/2372)

# Ansible

Ansible is a radically simple IT automation system. It handles
configuration management, application deployment, cloud provisioning,
ad-hoc task execution, network automation, and multi-node orchestration. Ansible makes complex
changes like zero-downtime rolling updates with load balancers easy. More information on the Ansible [website](https://ansible.com/).

## Design Principles

* Have an extremely simple setup process with a minimal learning curve.
* Manage machines quickly and in parallel.
* Avoid custom-agents and additional open ports, be agentless by
  leveraging the existing SSH daemon.
* Describe infrastructure in a language that is both machine and human
  friendly.
* Focus on security and easy auditability/review/rewriting of content.
* Manage new remote machines instantly, without bootstrapping any
  software.
* Allow module development in any dynamic language, not just Python.
* Be usable as non-root.
* Be the easiest IT automation system to use, ever.

## Use Ansible

You can install a released version of Ansible with `pip` or a package manager. See our
[installation guide](https://docs.ansible.com/ansible/latest/installation_guide/intro_installation.html) for details on installing Ansible
on a variety of platforms.

Power users and developers can run the `devel` branch, which has the latest
features and fixes, directly. Although it is reasonably stable, you are more likely to encounter
breaking changes when running the `devel` branch. We recommend getting involved
in the Ansible community if you want to run the `devel` branch.

## Quickstart Guide

Ansible can be installed from the terminal using pip, or on operating systems where pip is not available, the following pipx commands can be used: `pipx install --include-deps ansible` for the full Ansible package, `pipx install ansible-core` for a minimal package, and `pipx install ansible-core==<version number>` for a specific version (ex. 2.12.3). One of the basic functions of Ansible is building an inventory file to track a list of devices or servers. Two common formats for these files are INI (https://docs.fileformat.com/system/ini/) and YAML (https://www.cloudbees.com/blog/yaml-tutorial-everything-you-need-get-started). Groups and parent/child relationships can be made to help structure and organization.  Variables can be declared and parent/child relationships have inheritance functionality.  When defining groups in a static inventory, child groups must be defined in the same file or an error will be thrown.  Ansible has functionality that allows for dynamic inventories.  The program works smoothly with Cobbler, a Linux installation server.  The inventory script at https://raw.githubusercontent.com/ansible-community/contrib-scripts/main/inventory/cobbler.py is recomended, however, there are other options availabe.  Cobbler is available for free at https://cobbler.github.io/.  It is currently used by many companies as well as universities and government organizations.  Command line functionality allows for the use of multiple inventory source files simaltaneuously.  Executable files are treated as dynamic inventory sources while file extensions .orig, .bak, .ini, .cfg, .retry, .pyc, and .pyo are ignored. This list can be changed by using the `inventory_ignore_extensions` found in ansible.cfg or by setting the ANSIBLE_INVENTORY_IGNORE environmental variable.  When executing some commands in Ansible, it is required to specify which node or group should be effected.  They can be selected through the use of `ansible <pattern>`.  Ansible makes use of SSH as well.  Using `ssh-agent bash` along with `ssh-add ~/.ssh/id_rsa` is highly encouraged because the standard channel of communication does not allow a user to input a password manually. `--private-key` can be used to specify a pem file as well.  Other connections methods are available in various connection plugins as well as managing locally.

## Get Involved

* Read [Community Information](https://docs.ansible.com/ansible/latest/community) for all
  kinds of ways to contribute to and interact with the project,
  including mailing list information and how to submit bug reports and
  code to Ansible.
* Join a [Working Group](https://github.com/ansible/community/wiki),
  an organized community devoted to a specific technology domain or platform.
* Submit a proposed code update through a pull request to the `devel` branch.
* Talk to us before making larger changes
  to avoid duplicate efforts. This not only helps everyone
  know what is going on, but it also helps save time and effort if we decide
  some changes are needed.
* For a list of email lists, IRC channels and Working Groups, see the
  [Communication page](https://docs.ansible.com/ansible/latest/community/communication.html)

## Coding Guidelines

We document our Coding Guidelines in the [Developer Guide](https://docs.ansible.com/ansible/devel/dev_guide/). We particularly suggest you review:

* [Contributing your module to Ansible](https://docs.ansible.com/ansible/devel/dev_guide/developing_modules_checklist.html)
* [Conventions, tips, and pitfalls](https://docs.ansible.com/ansible/devel/dev_guide/developing_modules_best_practices.html)

## Branch Info

* The `devel` branch corresponds to the release actively under development.
* The `stable-2.X` branches correspond to stable releases.
* Create a branch based on `devel` and set up a [dev environment](https://docs.ansible.com/ansible/latest/dev_guide/developing_modules_general.html#common-environment-setup) if you want to open a PR.
* See the [Ansible release and maintenance](https://docs.ansible.com/ansible/devel/reference_appendices/release_and_maintenance.html) page for information about active branches.

## Roadmap

Based on team and community feedback, an initial roadmap will be published for a major or minor version (ex: 2.7, 2.8).
The [Ansible Roadmap page](https://docs.ansible.com/ansible/devel/roadmap/) details what is planned and how to influence the roadmap.

## Authors

Ansible was created by [Michael DeHaan](https://github.com/mpdehaan)
and has contributions from over 5000 users (and growing). Thanks everyone!

[Ansible](https://www.ansible.com) is sponsored by [Red Hat, Inc.](https://www.redhat.com)

## License

GNU General Public License v3.0 or later

See [COPYING](COPYING) to see the full text.
