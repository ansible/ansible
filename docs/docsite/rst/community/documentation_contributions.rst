.. _community_documentation_contributions:

*****************************************
Contributing to the Ansible Documentation
*****************************************

Ansible has a lot of documentation and a small team of writers. Community support helps us keep up with new features, fixes, and changes.

Improving the documentation is an easy way to make your first contribution to the Ansible project. You don't have to be a programmer, since our documentation is written in YAML (module documentation) or reStructured Text. If you're using Ansible, you know YAML - playbooks are written in YAML. And rST is mostly just text. You don't even need git experience, if you use the ``Edit on GitHub`` option.

If you find a typo, a broken example, a missing topic, or any other error or omission on docs.ansible.com, let us know. Here are some ways to support Ansible documentation:

.. contents:: Topics
   :local:

Editing docs directly on GitHub
===============================

For typos and other quick fixes, you can edit the documentation right from the documentation website. Look at the top right corner of this page. That ``Edit on GitHub`` link is available on every page in the documentation. If you have a GitHub account, you can submit a quick and easy pull request this way.

To submit a documentation PR from docs.ansible.com with ``Edit on GitHub``:

#. Click on ``Edit on GitHub``.
#. If you don't already have a fork of the ansible repo on your GitHub account, you'll be prompted to create one.
#. Fix the typo, update the example, or make whatever other change you have in mind.
#. Enter a commit message at the bottom of the GitHub page. The more specific, the better. For example, "fixes typo in my_module description".
#. Suggest the change. GitHub will handle branching and committing for you, and open Ansible's pull request template.
#. Fill out the PR template - include as much detail as appropriate for your change.
#. Submit the PR. Ansibot, our automated script, will add labels, cc: the docs maintainers, and kick off a CI testing run.
#. Keep an eye on your PR - the docs team may ask you for changes.

Opening a new issue and/or PR
=============================

If the problem you've noticed is too complex to fix with the ``Edit on GitHub`` option, please open an issue and/or a PR on the ``ansible/ansible`` repo.

A great documentation GitHub issue or PR includes:

- a specific title
- a detailed description of the problem (even for a PR - it's hard to evaluate a suggested change if we don't know what problem it's meant to solve)
- links to other information (related issues/PRs, external documentation, pages on docs.ansible.com, etc.)

Before you open a complex documentation PR
==========================================

If you make changes to the documentation, we recommend you build and test your branch locally before you open a pull request.

Building the documentation locally
----------------------------------

To build the documentation on your local machine, you need a few packages installed:

Once you have the required packages, navigate to ``ansible/docs/docsite`` and then select the build command you prefer:

To build all module documentation plus the rST files:

``make webdocs``

To build only the rST files:

``MODULES=none make webdocs``

To build a single rST file, you have two options:

1. You can use the make utility:

``make htmlsingle rst=<relative/path/to/your_file.rst>``

For example:

``make htmlsingle rst=dev_guide/developing_modules_documenting.rst``

This method compiles all the links but provides minimal log output.

2. You can use sphinx-build:

``sphinx-build [options] sourcedir outdir [filenames...]``

For example:

``sphinx-build -b html -c rst/ rst/dev_guide/ _build/html/dev_guide/ rst/dev_guide/developing_modules_documenting.rst``

This command doesn't incorporate other directories or files, so Sphinx won’t create reference links and you’ll get bogus ``undefined label`` warnings. But ``sphinx-build`` provides good syntax feedback, including warnings about indentation errors and ``x-string without end-string`` warnings. You can pass –a for all files, pass filenames to specify, or omit both to compile only new/changed files.

Testing the documentation locally
---------------------------------

To test your branch for rst errors, you need the ``rstcheck`` library:

``pip install rstcheck``

To test an individual file for rst errors:

``rstcheck myfile.rst``

To test a branch locally, move up to the top-level dir of the project and run:

``test/runner/ansible-test sanity docs/docsite/rst/dir/my_file.rst``

Reviewing open PRs and issues
=============================

You can also contribute by reviewing open documentation issues and PRs. To add a helpful review, please:

- include a comment - "looks good to me" only helps if we know why
- for issues, reproduce the problem
- for PRs, test the change

Joining the documentation working group
=======================================

The Documentation Working Group is just getting started, please visit the community repo for more information.
