[![PyPI version](https://img.shields.io/pypi/v/ansible-core.svg)](https://pypi.org/project/ansible-core)
[![Docs badge](https://img.shields.io/badge/docs-latest-brightgreen.svg)](https://docs.ansible.com/ansible/latest/)
[![Chat badge](https://img.shields.io/badge/chat-IRC-brightgreen.svg)](https://docs.ansible.com/ansible/devel/community/communication.html)
[![Build Status](https://dev.azure.com/ansible/ansible/_apis/build/status/CI?branchName=devel)](https://dev.azure.com/ansible/ansible/_build/latest?definitionId=20&branchName=devel)
[![Ansible Code of Conduct](https://img.shields.io/badge/code%20of%20conduct-Ansible-silver.svg)](https://docs.ansible.com/ansible/devel/community/code_of_conduct.html)
[![Ansible mailing lists](https://img.shields.io/badge/mailing%20lists-Ansible-orange.svg)](https://docs.ansible.com/ansible/devel/community/communication.html#mailing-list-information)
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

## Communication

Join the Ansible forum to ask questions, get help, and interact with the
community.

* [Get Help](https://forum.ansible.com/c/help/6): Find help or share your Ansible knowledge to help others.
  Use tags to filter and subscribe to posts, such as the following:
  * Posts tagged with [ansible](https://forum.ansible.com/tag/ansible)
  * Posts tagged with [ansible-core](https://forum.ansible.com/tag/ansible-core)
  * Posts tagged with [playbook](https://forum.ansible.com/tag/playbook)
* [Social Spaces](https://forum.ansible.com/c/chat/4): Meet and interact with fellow enthusiasts.
* [News & Announcements](https://forum.ansible.com/c/news/5): Track project-wide announcements including social events.
* [Bullhorn newsletter](https://docs.ansible.com/ansible/devel/community/communication.html#the-bullhorn): Get release announcements and important changes.

For more ways to get in touch, see [Communicating with the Ansible community](https://docs.ansible.com/ansible/devel/community/communication.html).

## Contribute to Ansible

* Check out the [Contributor's Guide](./.github/CONTRIBUTING.md).
* Read [Community Information](https://docs.ansible.com/ansible/devel/community) for all
  kinds of ways to contribute to and interact with the project,
  including how to submit bug reports and code to Ansible.
* Submit a proposed code update through a pull request to the `devel` branch.
* Talk to us before making larger changes
  to avoid duplicate efforts. This not only helps everyone
  know what is going on, but it also helps save time and effort if we decide
  some changes are needed.

## Coding Guidelines

We document our Coding Guidelines in the [Developer Guide](https://docs.ansible.com/ansible/devel/dev_guide/). We particularly suggest you review:

* [Contributing your module to Ansible](https://docs.ansible.com/ansible/devel/dev_guide/developing_modules_checklist.html)
* [Conventions, tips, and pitfalls](https://docs.ansible.com/ansible/devel/dev_guide/developing_modules_best_practices.html)

## Branch Info

* The `devel` branch corresponds to the release actively under development.
* The `stable-2.X` branches correspond to stable releases.
* Create a branch based on `devel` and set up a [dev environment](https://docs.ansible.com/ansible/devel/dev_guide/developing_modules_general.html#common-environment-setup) if you want to open a PR.
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
