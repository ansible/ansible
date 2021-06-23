.. _community_documentation_contributions:

*****************************************
Contributing to the Ansible Documentation
*****************************************

Ansible has a lot of documentation and a small team of writers. Community support helps us keep up with new features, fixes, and changes.

Improving the documentation is an easy way to make your first contribution to the Ansible project. You don't have to be a programmer, since our documentation is written in YAML (module documentation) or `reStructuredText <http://docutils.sourceforge.net/rst.html>`_ (rST). If you're using Ansible, you already use YAML in your playbooks. And rST is mostly just text. You don't even need git experience, if you use the ``Edit on GitHub`` option.

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
#. Enter a commit message in the first rectangle under the heading ``Propose file change`` at the bottom of the GitHub page. The more specific, the better. For example, "fixes typo in my_module description". You can put more detail in the second rectangle if you like. Leave the ``+label: docsite_pr`` there.
#. Submit the suggested change by clicking on the green "Propose file change" button. GitHub will handle branching and committing for you, and open a page with the heading "Comparing Changes".
#. Click on ``Create pull request`` to open the PR template.
#. Fill out the PR template, including as much detail as appropriate for your change. You can change the title of your PR if you like (by default it's the same as your commit message). In the ``Issue Type`` section, delete all lines except the ``Docs Pull Request`` line.
#. Submit your change by clicking on ``Create pull request`` button.
#. Be patient while Ansibot, our automated script, adds labels, pings the docs maintainers, and kicks off a CI testing run.
#. Keep an eye on your PR - the docs team may ask you for changes.

Reviewing open PRs and issues
=============================

You can also contribute by reviewing open documentation `issues <https://github.com/ansible/ansible/issues?utf8=%E2%9C%93&q=is%3Aissue+is%3Aopen+label%3Adocs>`_ and `PRs <https://github.com/ansible/ansible/pulls?utf8=%E2%9C%93&q=is%3Apr+is%3Aopen+label%3Adocs>`_. To add a helpful review, please:

- Include a comment - "looks good to me" only helps if we know why.
- For issues, reproduce the problem.
- For PRs, test the change.

Opening a new issue and/or PR
=============================

If the problem you've noticed is too complex to fix with the ``Edit on GitHub`` option, and no open issue or PR already documents the problem, please open an issue and/or a PR on the ``ansible/ansible`` repo.

A great documentation GitHub issue or PR includes:

- a specific title
- a detailed description of the problem (even for a PR - it's hard to evaluate a suggested change unless we know what problem it's meant to solve)
- links to other information (related issues/PRs, external documentation, pages on docs.ansible.com, and so on.)

Before you open a complex documentation PR
==========================================

If you make multiple changes to the documentation, or add more than a line to it, before you open a pull request, please:

#. Check that your text follows our :ref:`style_guide`.
#. Test your changes for rST errors.
#. Build the page, and preferably the entire documentation site, locally.

To work with documentation on your local machine, you need to have python-3.5 or greater and the
following packages installed:

- gcc
- jinja2
- libyaml
- Pygments >= 2.4.0
- pyparsing
- PyYAML
- rstcheck
- six
- sphinx
- sphinx-notfound-page
- straight.plugin

.. note::

    On macOS with Xcode, you may need to install ``six`` and ``pyparsing`` with ``--ignore-installed`` to get versions that work wth ``sphinx``.

.. _testing_documentation_locally:

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

To build a single rST file with the make utility:

.. code-block:: bash

   make htmlsingle rst=path/to/your_file.rst

For example:

.. code-block:: bash

   make htmlsingle rst=community/documentation_contributions.rst

This process compiles all the links but provides minimal log output. If you're writing a new page or want more detailed log output, refer to the instructions on :ref:`build_with_sphinx-build`

.. note::

    ``make htmlsingle`` adds ``rst/`` to the beginning of the path you provide in ``rst=``, so you can't type the filename with autocomplete. Here are the error messages you will see if you get this wrong:

      - If you run ``make htmlsingle`` from the ``docs/docsite/rst/`` directory: ``make: *** No rule to make target `htmlsingle'.  Stop.``
      - If you run ``make htmlsingle`` from the ``docs/docsite/`` directory with the full path to your rST document: ``sphinx-build: error: cannot find files ['rst/rst/community/documentation_contributions.rst']``.


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

.. _build_with_sphinx-build:

Building rST files with ``sphinx-build``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Advanced users can build one or more rST files with the sphinx utility directly. ``sphinx-build`` returns misleading ``undefined label`` warnings if you only build a single page, because it does not create internal links. However, ``sphinx-build`` returns more extensive syntax feedback, including warnings about indentation errors and ``x-string without end-string`` warnings. This can be useful, especially if you're creating a new page from scratch. To build a page or pages with ``sphinx-build``:

.. code-block:: bash

  sphinx-build [options] sourcedir outdir [filenames...]

You can specify filenames, or ``–a`` for all files, or omit both to compile only new/changed files.

For example:

.. code-block:: bash

  sphinx-build -b html -c rst/ rst/dev_guide/ _build/html/dev_guide/ rst/dev_guide/developing_modules_documenting.rst

Running the final tests
^^^^^^^^^^^^^^^^^^^^^^^

When you submit a documentation pull request, automated tests are run. Those same tests can be run locally. To do so, navigate to the repository's top directory and run:

.. code-block:: bash

  make clean &&
  bin/ansible-test sanity --test docs-build &&
  bin/ansible-test sanity --test rstcheck

Unfortunately, leftover rST-files from previous document-generating can occasionally confuse these tests. It is therefore safest to run them on a clean copy of the repository, which is the purpose of ``make clean``. If you type these three lines one at a time and manually check the success of each, you do not need the ``&&``.

Joining the documentation working group
=======================================

The Documentation Working Group is just getting started, please visit the `community repo <https://github.com/ansible/community>`_ for more information.

The Documentation Working Group (DaWGs) meets weekly on Tuesdays on the #ansible-docs channel on the `libera.chat IRC network <https://libera.chat/>`_. For more information, including links to our agenda and a calendar invite, please visit the `working group page in the community repo <https://github.com/ansible/community/wiki/Docs>`_.

.. seealso::
   :ref:`More about testing module documentation <testing_module_documentation>`
   :ref:`More about documenting modules <module_documenting>`
