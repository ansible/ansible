.. _community_documentation_contributions:

*****************************************
Contributing to the Ansible Documentation
*****************************************

Ansible has a lot of documentation and a small team of writers. Community support helps us keep up with new features, fixes, and changes.

Improving the documentation is an easy way to make your first contribution to the Ansible project. You don't have to be a programmer, since our documentation is written in YAML (module documentation) or reStructured Text. If you're using Ansible, you know YAML - playbooks are written in YAML. And rST is mostly just text. You don't even need git experience, if you use the ``Edit on GitHub`` option.

If you find a typo, a broken example, a missing topic, or any other error or omission on this documentation website, let us know. Here are some ways to support Ansible documentation:

.. contents::
   :local:

Editing docs directly on GitHub
===============================

For typos and other quick fixes, you can edit the documentation right from the site. Look at the top right corner of this page. That ``Edit on GitHub`` link is available on every page in the documentation. If you have a GitHub account, you can submit a quick and easy pull request this way.

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
- a detailed description of the problem (even for a PR - it's hard to evaluate a suggested change unless we know what problem it's meant to solve)
- links to other information (related issues/PRs, external documentation, pages on docs.ansible.com, etc.)

Before you open a complex documentation PR
==========================================

If you make multiple changes to the documentation, or add more than a line to it, before you open a pull request, please:

#. Check that your text follows our :ref:`style_guide`.
#. Test your changes for rST errors.
#. Build the page, and preferably the entire documentation site, locally.

To work with documentation on your local machine, you need the following packages installed:

.. code-block:: none

   - libyaml
   - pyyaml
   - nose
   - six
   - tornado
   - pyparsing
   - gcc
   - jinja2
   - rstcheck
   - sphinx

.. note::

    On macOS with Xcode, you may need to install ``six`` and ``pyparsing`` with ``--ignore-installed`` to get versions that work wth ``sphinx``.

Testing the documentation locally
---------------------------------

To test an individual file for rST errors:

.. code-block:: bash

   rstcheck changed_file.rst

Building the documentation locally
----------------------------------

Building the documentation is the best way to check for errors and review your changes. Once `rstcheck` runs with no errors, navigate to ``ansible/docs/docsite`` and then build the page(s) you want to review.

Building a single rST page
^^^^^^^^^^^^^^^^^^^^^^^^^^

To build a single rST file, you have two options:

1. Building an rST file with the make utility:

.. code-block:: bash

   make htmlsingle rst=path/to/your_file.rst

For example:

.. code-block:: bash

   make htmlsingle rst=community/documentation_contributions.rst

This method compiles all the links but provides minimal log output.

.. note::

    ``make htmlsingle`` adds ``rst/`` to the beginning of the path you provide in ``rst=``, so you can't type the filename with autocomplete. If you run ``make htmlsingle`` from the ``docs/docsite/rst/` directory, you'll get ``make: *** No rule to make target `htmlsingle'.  Stop.`` If you run it from ``docs/docsite/`` and provide the full path, you'll get ``sphinx-build: error: cannot find files ['rst/rst/community/documentation_contributions.rst']``.

2. Building an rST file with sphinx-build:

.. code-block:: bash

   sphinx-build [options] sourcedir outdir [filenames...]

You can specify filenames, or ``–a`` for all files, or omit both to compile only new/changed files.

For example:

.. code-block:: bash

   sphinx-build -b html -c rst/ rst/dev_guide/ _build/html/dev_guide/ rst/dev_guide/developing_modules_documenting.rst

If you build a single file, Sphinx won’t create reference links and you’ll get bogus ``undefined label`` warnings. But ``sphinx-build`` provides good syntax feedback, including warnings about indentation errors and ``x-string without end-string`` warnings.

Building all the rST pages
^^^^^^^^^^^^^^^^^^^^^^^^^^

To build all the rST files without any module documentation:

.. code-block:: bash

   MODULES=none make webdocs

Building module docs and rST pages
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To build documentation for a few modules plus all the rST files, use a comma-separated list:

.. code-block:: bash

   MODULES=one_module,another_module make webdocs

To build all the module documentation plus all the rST files:

.. code-block:: bash

   make webdocs

Reviewing open PRs and issues
=============================

You can also contribute by reviewing open documentation issues and PRs. To add a helpful review, please:

- Include a comment - "looks good to me" only helps if we know why.
- For issues, reproduce the problem.
- For PRs, test the change.

Joining the documentation working group
=======================================

The Documentation Working Group is just getting started, please visit the `community repo <https://github.com/ansible/community>`_ for more information.

.. seealso::
   :ref:`More about testing module documentation <testing_documentation>`
   :ref:`More about documenting modules <module_documenting>`
