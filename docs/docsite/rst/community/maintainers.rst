.. _maintainers:

****************************
Module Maintainer Guidelines
****************************

.. contents:: Topics

Thank you for being a maintainer of part of Ansible's codebase. This guide provides module maintainers an overview of their responsibilities, resources for additional information, and links to helpful tools.

In addition to the information below, module maintainers should be familiar with:

* :ref:`General Ansible community development practices <ansible_community_guide>`
* Documentation on :ref:`module development <developing_modules>`


Maintainer Responsibilities
===========================

When you contribute a new module to the `ansible/ansible <https://github.com/ansible/ansible>`_ repository, you become the maintainer for that module once it has been merged. Maintainership empowers you with the authority to accept, reject, or request revisions to pull requests on your module -- but as they say, "with great power comes great responsibility."

Maintainers of Ansible modules are expected to provide feedback, responses, or actions on pull requests or issues to the module(s) they maintain in a reasonably timely manner.

It is also recommended that you occasionally revisit the `contribution guidelines <https://github.com/ansible/ansible/blob/devel/.github/CONTRIBUTING.md>`_, as they are continually refined. Occasionally, you may be requested to update your module to move it closer to the general accepted standard requirements. We hope for this to be infrequent, and will always be a request with a fair amount of lead time (ie: not by tomorrow!).

Finally, following the `ansible-devel <https://groups.google.com/forum/#!forum/ansible-devel>`_ mailing list can be a great way to participate in the broader Ansible community, and a place where you can influence the overall direction, quality, and goals of Ansible and its modules. If you're not on this relatively low-volume list, please join us here: https://groups.google.com/forum/#!forum/ansible-devel

The Ansible community hopes that you will find that maintaining your module is as rewarding for you as having the module is for the wider community.

Pull Requests, Issues, and Workflow
===================================

Pull Requests
-------------

Module pull requests are located in the `main Ansible repository <https://github.com/ansible/ansible/pulls>`_.

Because of the high volume of pull requests, notification of PRs to specific modules are routed by an automated bot to the appropriate maintainer for handling. It is recommended that you set an appropriate notification process to receive notifications which mention your GitHub ID.

Issues
------

Issues for modules, including bug reports, documentation bug reports, and feature requests, are tracked in the `ansible repository <https://github.com/ansible/ansible/issues>`_.

Issues for modules are routed to their maintainers via an automated process. This process is still being refined, and currently depends upon the issue creator to provide adequate details (specifically, providing the proper module name) in order to route it correctly. If you are a maintainer of a specific module, it is recommended that you periodically search module issues for issues which mention your module's name (or some variation on that name), as well as setting an appropriate notification process for receiving notification of mentions of your GitHub ID.

PR Workflow
-----------

Automated routing of pull requests is handled by a tool called `Ansibot <https://github.com/ansible/ansibullbot>`_.

Being moderately familiar with how the workflow behind the bot operates can be helpful to you, and -- should things go awry -- your feedback can be helpful to the folks that continually help Ansibullbot to evolve.

A detailed explanation of the PR workflow can be seen in the :doc:`development_process`

Maintainers (BOTMETA.yml)
-------------------------

The full list of maintainers is located in `BOTMETA.yml <https://github.com/ansible/ansible/blob/devel/.github/BOTMETA.yml>`_.

Changing Maintainership
-----------------------

Communities change over time, and no one maintains a module forever. If you'd like to propose an additional maintainer for your module, please submit a PR to ``BOTMETA.yml`` with the GitHub username of the new maintainer.

If you'd like to step down as a maintainer, please submit a PR to the ``BOTMETA.yml`` removing your GitHub ID from the module in question. If that would leave the module with no maintainers, put "ansible" as the maintainer.  This will indicate that the module is temporarily without a maintainer, and the Ansible community team will search for a new maintainer.

Tools and other Resources
=========================

* `PRs in flight, organised by directory <https://ansible.sivel.net/pr/byfile.html>`_.
* Ansibullbot: https://github.com/ansible/ansibullbot
* :doc:`development_process`
