[![PyPI version](https://img.shields.io/pypi/v/ansible-core.svg)](https://pypi.org/project/ansible-core)
[![Docs badge](https://img.shields.io/badge/docs-latest-brightgreen.svg)](https://docs.ansible.com/ansible/latest/)
[![Chat badge](https://img.shields.io/badge/chat-IRC-brightgreen.svg)](https://docs.ansible.com/ansible/latest/community/communication.html)
[![Build Status](https://dev.azure.com/ansible/ansible/_apis/build/status/CI?branchName=devel)](https://dev.azure.com/ansible/ansible/_build/latest?definitionId=20&branchName=devel)
[![Ansible Code of Conduct](https://img.shields.io/badge/code%20of%20conduct-Ansible-silver.svg)](https://docs.ansible.com/ansible/latest/community/code_of_conduct.html)
[![Ansible mailing lists](https://img.shields.io/badge/mailing%20lists-Ansible-orange.svg)](https://docs.ansible.com/ansible/latest/community/communication.html#mailing-list-information)
[![Repository License](https://img.shields.io/badge/license-GPL%20v3.0-brightgreen.svg)](COPYING)
[![Ansible CII Best Practices certification](https://bestpractices.coreinfrastructure.org/projects/2372/badge)](https://bestpractices.coreinfrastructure.org/projects/2372)

Ansible: Simplifying IT Automation

Ansible is an incredibly user-friendly IT automation system that revolutionizes tasks like configuration management, application deployment, cloud provisioning, ad-hoc task execution, network automation, and multi-node orchestration. This versatile tool enables you to effortlessly handle complex tasks, such as zero-downtime rolling updates with load balancers. For more in-depth information, visit the Ansible website.

#Design Principles

    Streamlined Setup: Ansible boasts an extraordinarily simple setup process with a minimal learning curve.
    Efficient Management: It allows you to manage machines quickly and in parallel, boosting productivity.
    Agentless Approach: Say goodbye to custom agents and additional open ports. Ansible leverages the existing SSH daemon, enhancing security and simplicity.
    Human-Friendly Language: You can describe infrastructure in a language that's both understandable by machines and humans.
    Security Focus: Ansible prioritizes security, making auditing, reviewing, and rewriting content easy.
    Instant Remote Management: Managing new remote machines is a breeze, without the need for software bootstrapping.
    Language Flexibility: Module development is supported in any dynamic language, not restricted to Python.
    Non-Root Usage: Ansible can be used as a non-root user, providing flexibility and security.
    User-Friendly: It aims to be the most user-friendly IT automation system available.

#Using Ansible

You can install Ansible by choosing either a released version using pip or a package manager. Refer to our installation guide for comprehensive instructions on installing Ansible across various platforms.

For power users and developers, the 'devel' branch is available, offering the latest features and fixes. However, please be aware that while reasonably stable, running the 'devel' branch may introduce breaking changes. We encourage community involvement if you wish to run the 'devel' branch.

#Get Involved

    Community Interaction: Explore our Community Information to learn about ways you can contribute to the project, including details on mailing lists, bug reporting, and code submissions.
    Working Groups: Join a Working Group dedicated to specific technology domains or platforms.
    Code Contributions: Submit proposed code updates through pull requests to the 'devel' branch.
    Collaboration: Before making significant changes, it's advisable to discuss them with us to prevent duplication of efforts and save time. This helps keep everyone informed.
    Communication Channels: Find email lists, IRC channels, and Working Groups on the Communication page.

#Coding Guidelines

Our Coding Guidelines are documented in the Developer Guide. We particularly recommend reviewing:

    Contributing Your Module to Ansible
    Conventions, Tips, and Pitfalls

#Branch Information

    The 'devel' branch corresponds to the actively developed release.
    The 'stable-2.X' branches represent stable releases.
    To open a PR, create a branch based on 'devel' and set up a development environment.
    Refer to the Ansible release and maintenance page for information on active branches.

#Roadmap

Based on feedback from our team and the community, we regularly publish roadmaps for major and minor versions (e.g., 2.7, 2.8). The Ansible Roadmap page outlines what's planned and how you can influence the roadmap.

#Authors

Ansible was conceived by Michael DeHaan and has received contributions from over 5000 users and counting. We extend our gratitude to everyone who has contributed to this project.

#Sponsorship

Ansible is proudly sponsored by Red Hat, Inc.

#License

Released under the GNU General Public License v3.0 or later. Refer to the COPYING file for the complete text.
