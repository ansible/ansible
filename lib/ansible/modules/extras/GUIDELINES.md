# Module Maintainer Guidelines 

Thank you for being a maintainer of one of the modules in ansible-modules-extras! This guide provides module maintainers an overview of their responsibilities, resources for additional information, and links to helpful tools.

In addition to the information below, module maintainers should be familiar with:
* General Ansible community development practices (http://docs.ansible.com/ansible/community.html)
* Documentation on module development (http://docs.ansible.com/ansible/developing_modules.html)
* Any namespace-specific module guidelines (identified as GUIDELINES.md in the appropriate file tree).

***

# Maintainer Responsibilities

When you contribute a new module to the ansible-modules-extras repository, you become the maintainer for that module once it has been merged. Maintainership empowers you with the authority to accept, reject, or request revisions to pull requests on your module -- but as they say, "with great power comes great responsibility."

Maintainers of Ansible modules are expected to provide feedback, responses, or actions on pull requests or issues to the module(s) they maintain in a reasonably timely manner.

It is also recommended that you occasionally revisit the [contribution guidelines](https://github.com/alikins/ansible-modules-extras/commit/c87795da5b0c95c67fea1608a5a2a4ec54cb3905), as they are continually refined. Occasionally, you may be requested to update your module to move it closer to the general accepted standard requirements; we hope for this to be infrequent, and will always be a request with a fair amount of lead time (ie: not by tomorrow!). 

Finally, following the ansible-devel mailing list can be a great way to participate in the broader Ansible community, and a place where you can influence the overall direction, quality, and goals of the Extras modules repository. If you're not on this relatively low-volume list, please join us here: https://groups.google.com/forum/#!forum/ansible-devel

The Ansible community hopes that you will find that maintaining your module is as rewarding for you as having the module is for the wider community.

***

# Pull Requests, Issues, and Workflow

## Pull Requests

Module pull requests are located in the [ansible-modules-extras repository](https://github.com/ansible/ansible-modules-extras/pulls).

Because of the high volume of pull requests, notification of PRs to specific modules are routed by an automated bot to the appropriate maintainer for handling. It is recommended that you set an appropriate notification process to receive notifications which mention your GitHub ID.

## Issues

Issues for modules, including bug reports, documentation bug reports, and feature requests, are tracked in the [ansible-modules-extras repository](https://github.com/ansible/ansible-modules-extras/issues).

 Issues for modules are routed to their maintainers via an automated process. This process is still being refined, and currently depends upon the issue creator to provide adequate details (specifically, providing the proper module name) in order to route it correctly. If you are a maintainer of a specific module, it is recommended that you periodically search module issues for issues which mention your module's name (or some variation on that name), as well as setting an appropriate notification process for receiving notification of mentions of your GitHub ID.

## PR Workflow 

Automated routing of pull requests is handled by a tool called [Ansibullbot](https://github.com/ansible/ansibullbot). (You could say that he moooo-ves things around.)

Being moderately familiar with how the workflow behind the bot operates can be helpful to you, and -- should things go awry -- your feedback can be helpful to the folks that continually help Ansibullbot to evolve.

A detailed explanation of the PR workflow can be seen here: https://github.com/ansible/community/blob/master/PR-FLOW.md 

***

# Extras maintainers list

The full list of maintainers for modules in ansible-modules-extras is located here:
https://github.com/ansible/ansibullbot/blob/master/MAINTAINERS-EXTRAS.txt

## Changing Maintainership

Communities change over time, and no one maintains a module forever. If you'd like to propose an additional maintainer for your module, please submit a PR to the maintainers file with the Github ID of the new maintainer.

If you'd like to step down as a maintainer, please submit a PR to the maintainers file removing your Github ID from the module in question. If that would leave the module with no maintainers, put "ansible" as the maintainer.  This will indicate that the module is temporarily without a maintainer, and the Ansible community team will search for a new maintainer.

***

# Tools and other Resources

## Useful tools
* https://ansible.sivel.net/pr/byfile.html -- a full list of all open Pull Requests, organized by file. 

## Other Resources

* Module maintainer list: https://github.com/ansible/ansibullbot/blob/master/MAINTAINERS-EXTRAS.txt
* Ansibullbot: https://github.com/ansible/ansibullbot
* Triage / pull request workflow and information, including definitions for Labels in GitHub: https://github.com/ansible/community/blob/master/PR-FLOW.md
