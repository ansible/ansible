Information for submitting a group of modules
=============================================

.. contents:: Topics

Submitting a group of modules
`````````````````````````````

This section discusses how to get multiple related modules into Ansible.

This document is intended for both companies wishing to add modules for their own products as well as users of 3rd party products wishing to add Ansible functionality.

It's based on module development best practices that the Ansible core team and community have accumulated.


Before you start coding
```````````````````````

Although it's tempting to get straight into coding, there are a few things to be aware of first. This list of prerequisites is designed to help ensure that you develop high-quality modules that flow easily through the review process and get into Ansible more quickly.

* Read though all the pages linked off :doc:`developing_modules`; paying particular focus to the :doc:`developing_modules_checklist`.
* For new modules going into Ansible 2.4 we are raising the bar so they must be PEP 8 compliant. See :doc:`testing_pep8` for more information.
* Starting with Ansible version 2.4, all new modules must support Python 2.6 and Python 3.5+. If this is an issue, please contact us (see the "Speak to us" section later in this document to learn how).
* All modules shipped with Ansible must be done so under the GPLv3 license. Files under the ``lib/ansible/module_utils/`` directory should be done so under the BSD license.
* Have a look at the existing modules and how they've been named in the :doc:`../list_of_all_modules`, especially in the same functional area (such as cloud, networking, databases).
* Shared code can be placed into ``lib/ansible/module_utils/``
* Shared documentation (for example describing common arguments) can be placed in ``lib/ansible/utils/module_docs_fragments/``.
* With great power comes great responsibility: Ansible module maintainers have a duty to help keep modules up to date. As with all successful community projects, module maintainers should keep a watchful eye for reported issues and contributions.
* Although not required, unit and/or integration tests are strongly recommended. Unit tests are especially valuable when external resources (such as cloud or network devices) are required. For more information see :doc:`testing` and the `Testing Working Group <https://github.com/ansible/community/blob/master/meetings/README.md>`_.
  * Starting with Ansible 2.4 all :doc:`../list_of_network_modules` MUST have unit tests.


Naming Convention
`````````````````

As you may have noticed when looking under ``lib/ansible/modules/`` we support up to two directories deep (but no deeper), e.g. `databases/mysql`. This is used to group files on disk as well as group related modules into categories and topics the Module Index, for example: :doc:`../list_of_database_modules`.

The directory name should represent the *product* or *OS* name, not the company name.

Each module should have the above (or similar) prefix; see existing :doc:`../list_of_all_modules` for existing examples.

**Note:**

* File and directory names are always in lower case
* Words are separated with an underscore (``_``) character
* Module names should be in the singular, rather than plural, eg ``command`` not ``commands``


Speak to us
```````````

Circulating your ideas before coding is a good way to help you set off in the right direction.

After reading the "Before you start coding" section you will hopefully have a reasonable idea of the structure of your modules.

We've found that writing a list of your proposed module names and a one or two line description of what they will achieve and having that reviewed by Ansible is a great way to ensure the modules fit the way people have used Ansible Modules before, and therefore make them easier to use.


Where to get support
````````````````````

Ansible has a thriving and knowledgeable community of module developers that is a great resource for getting your questions answered.

On :doc:`../community` you can find how to:

* Subscribe to the Mailing Lists - We suggest "Ansible Development List" (for codefreeze info) and "Ansible Announce list"
* ``#ansible-devel`` - We have found that IRC ``#ansible-devel`` on FreeNodes IRC network works best for module developers so we can have an interactive dialogue.
* IRC meetings - Join the various weekly IRC meetings `meeting schedule and agenda page <https://github.com/ansible/community/blob/master/meetings/README.md>`_


Your First Pull Request
````````````````````````

Now that you've reviewed this document, you should be ready to open your first pull request.

The first PR is slightly different to the rest because it:

* defines the namespace
* provides a basis for detailed review that will help shape your future PRs
* may include shared documentation (`docs_fragments`) that multiple modules require
* may include shared code (`module_utils`) that multiple modules require


The first PR should include the following files:

* ``lib/ansible/modules/$category/$topic/__init__.py`` - An empty file to initialize namespace and allow Python to import the files. *Required new file*
* ``lib/ansible/modules/$category/$topic/$yourfirstmodule.py`` - A single module. *Required new file*
* ``lib/ansible/utils/module_docs_fragments/$topic.py`` - Code documentation, such as details regarding common arguments. *Optional new file*
* ``lib/ansible/module_utils/$topic.py`` - Code shared between more than one module, such as common arguments. *Optional new file*
*  ``docs/docsite/rst/dev_guide/developing_module_utilities.rst`` - Document your new `module_utils` file. *Optional update to existing file*

And that's it.

Before pushing your PR to GitHub it's a good idea to review the :doc:`developing_modules_checklist` again.

After publishing your PR to https://github.com/ansible/ansible, a Shippable CI test should run within a few minutes. Check the results (at the end of the PR page) to ensure that it's passing (green). If it's not passing, inspect each of the results. Most of the errors should be self-explanatory and are often related to badly formatted documentation (see :doc:`../YAMLSyntax`) or code that isn't valid Python 2.6  or valid Python 3.5 (see :doc:`developing_python3`). If you aren't sure what a Shippable test message means, copy it into the PR along with a comment and we will review.

If you need further advice, consider join the ``#ansible-devel`` IRC channel (see how in the "Where to get support").


We have a ``ansibullbot`` helper that comments on GitHub Issues and PRs which should highlight important information.


Subsequent PRs
``````````````

By this point you first PR that defined the module namespace should have been merged. You can take the lessons learned from the first PR and apply it to the rest of the modules.

Raise exactly one PR per module for the remaining modules.

Over the years we've experimented with different sized module PRs, ranging from one module to many tens of modules, and during that time we've found the following:

* A PR with a single file gets a higher quality review
* PRs with multiple modules are harder for the creator to ensure all feedback has been applied
* PRs with many modules take a lot more work to review, and tend to get passed over for easier-to-review PRs.

You can raise up to five PRs at one (5 PRs = 5 new modules) **after** your first PR has been merged. We've found this is a good batch size to keep the review process flowing.

Finally
```````

Now that your modules are integrated there are a few bits of housekeeping to be done

**Bot Meta**
Update `Ansibullbot` so it knows who to notify if/when bugs or PRs are raised against your modules
`BOTMETA.yml <https://github.com/ansible/ansible/blob/devel/.github/BOTMETA.yml>`_.

If there are multiple people that can be notified, please list them. That avoids waiting on a single person who may be unavailable for any reason. Note that in `BOTMETA.yml` you can take ownership of an entire directory.


**Review Module web docs**
Review the autogenerated module documentation for each of your modules, found in `Module Docs <http://docs.ansible.com/ansible/modules_by_category.html>`_ to ensure they are correctly formatted. If there are any issues please fix by raising a single PR.

If the module documentation hasn't been published live yet, please let a member of the Ansible Core Team know in the ``#ansible-devel`` IRC channel.


New to Git or GitHub
````````````````````

We realise this may be your first use of Git or GitHub. The following guides may be of use:

* `How to create a fork of ansible/ansible <https://help.github.com/articles/fork-a-repo/>`_
* `How to sync (update) your fork <https://help.github.com/articles/syncing-a-fork/>`_
* `How to create a Pull Request (PR) <https://help.github.com/articles/about-pull-requests/>`_

Please note that in the Ansible Git Repo the main branch is called ``devel`` rather than ``master``, which is used in the official GitHub documentation

After your first PR has been merged ensure you "sync your fork" with ``ansible/ansible`` to ensure you've pulled in the directory structure and and shared code or documentation previously created.

As stated in the GitHub documentation, always use feature branches for your PRs, never commit directly into `devel`.
