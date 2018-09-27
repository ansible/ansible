.. _community_documentation_contributions:

*****************************************
Contributing to the Ansible Documentation
*****************************************

.. contents:: Topics
   :local:

Improving the documentation is an easy way to make your first contribution to the Ansible project. You don't have to be a programmer, since the documentation is written in either YAML (module documentation) or reStructured Text. If you're using Ansible, you know YAML - playbooks are written in YAML. And rST is mostly just text. You don't even need git experience, if you use the ``Edit on GitHub`` option.

If you find a typo, a broken example, a missing topic, or any other error or omission on docs.ansible.com, we hope you'll let us know. Here are some ways to support Ansible documentation:

The "Edit on GitHub" option
===========================

For typos and other quick fixes, you can edit the documentation right from docs.ansible.com. Look at the top right corner of this page. That ``Edit on GitHub`` link is available on every page in the documentation. If you have a GitHub account, you can submit a quick and easy pull request this way.

To submit a documentation PR from docs.ansible.com with ``Edit on GitHub``:

#. Click on ``Edit on GitHub``.
#. If you don't already have a fork of the ansible repo on your GitHub account, you'll be prompted to create one.
#. Fix the typo, update the example, or make whatever other change you have in mind.
#. Enter a commit message at the bottom of the GitHub page. The more specific, the better. For example, "fixes typo in my_module description".
#. Suggest the change. GitHub will handle branching and committing for you, and open Ansible's pull request template.
#. Fill out the PR template - include as much detail as appropriate for your change.
#. Submit the PR. Ansibot, our automated script, will add labels, cc: the docs maintainers, and kick off a CI testing run.
#. Keep an eye on your PR - the docs team may ask you for changes.

Review open PRs and issues
==========================

Ansible has a lot of documentation and a small team of writers. Community support helps us keep up with documentation changes. You can join in by reviewing open documentation issues and PRs. To add a helpful review, please:

- include a comment - "looks good to me" only helps if we know why
- for issues, reproduce the problem
- for PRs, test the change

Open a new issue and/or PR
==========================

If the problem you've noticed is too complex to fix with the ``Edit on GitHub`` option, please open an issue and/or a PR on the ``ansible/ansible`` repo.

A great documentation GitHub issue or PR includes:

- a specific title
- a detailed description of the problem (even for a PR - it's hard to evaluate a suggested change if we don't know what problem it's meant to solve)
- links to other information (related issues/PRs, external documentation, pages on docs.ansible.com, etc.)

Join the documentation working group
====================================

The Documentation Working Group is just getting started, please visit the community repo for more information.
