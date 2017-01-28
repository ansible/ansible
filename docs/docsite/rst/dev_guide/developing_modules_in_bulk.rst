Partner information for submitting modules
==========================================

.. contents:: Topics

.. _module_dev_welcome:

Welcome
```````
This section discusses some of the specifics around getting multiple related modules into Ansible.

The information in the page is useful for both companies wishing to add modules for their own products, as well as for users of 3rd party products wishing to add Ansible support.

It's based on the knowledge on the Core Team and Community on what we've found is the best practice for the module developer(s), the Community, and the Ansible Core Team.



Before you start coding
```````````````````````

Although it's tempting to get straight into coding, there are a few things to be aware of first. This list has been drawn to ensure the best modules are developed and to speed up the review process, which means your modules get accepted into Ansible with minimal fuss.

* Read though all the pages linked off :doc:`developing_modules`, paying particular focus to the :doc:`developing_modules_checklist`.
* For new modules going into Ansible 2.4 we are raising the bar so they must pass `pep8 --ignore=E402 --max-line-length=160` cleanly.
* All new modules going into Ansible 2.3 must support Python 2.4+ and Python 3.5+. For Ansible 2.4 the requirement will change to Python and Python 3.5+. If this is an issues mention it in the "Speak to us" section later in this document.
* Understand that all modules shipped with Ansible MUST be done so under the GPLv3 license. Files under the `lib/ansible/module_utils/` directory must be under the FIXME license.
* Have a look at the existing modules, especially in the same functional area (such as cloud, networking, databases) in the :doc:`../list_of_all_modules` for a list of existing modules and how they've been named.

# FIXME Add details about docs_fragments and module_utils (once the other docs are tidied up this can be simplified as a link to those existing sections

Naming Convention
`````````````````

As you may have noticed when looking under `lib/ansible/modules/` we support up to two directories deep (but no deeper), e.g. `databases/mysql`. This is used to group files on disk as well as group related modules in the Module Index, for example: :doc:`../list_of_database_modules`.

The directory name should represent the **product** or **OS** name, not the company name.

Each module should have the above (or similar) prefix, see existing :doc:`../list_of_all_modules` for existing examples.

Note
* File and directory names are always in lower case
* Words are separated with an underscore (`_`) character


Speak to us
```````````

Circulating your ideas before coding is a good way to help you set off in the right direction.

After reading the "Before you start coding" section you will hopefully have a reasonable idea of the structure of your modules.

We've found that writing a list of your proposed module names and a one or two line description of what they will achive and having that reviewed by Ansible is a great way to ensure the modules fit the way people have used Ansible Modules before, and therefore make them easier to use

FIXME: How do we want to know the above, will everyone had a named contact at Ansible, what about if it's the community, rather than a vendor?
FIXME: Some light weight review process of the above
FIXME: I (gundalow) isn't sure if we want to preasure the Public Core Meetings with this, though that is one recommended way for the community to reach the Core Team.

Where to get support
````````````````````
Ansible has a very strong community, and we trust you as module developers will help grow.

The community is a great pool of resource and knowledge.
# FIXME Links to page that has community info in

Subscribe to (at least) announce and devel. This is so you will be aware of deadlines regarding codefreeze in the lead upto releases and other important information

We have found that IRC `#ansible-devel` works best for module developers so we can have an interactive dialogue.
Code and questions can be put into pastebin/gist.github.com, then you can reference that URL in chat.


Your First PR
``````````````

Assuming you've been through the rest of this document, and not just skipped ahead, you should now be ready to raise your first PR.

The first PR is slightly different to the rest as:
* it defines the namespace
* it provides a bases for detailed review that will help shape your future PRs
* it may include shared documentation (`docs_fragments`) that multiple modules require
* it may include shared code (`module_utils`) that multiple modules require


The first PR should include the following files:
* `lib/ansible/modules/$area/$prefix/__init__.py` - An empty file to initilize namespace and allow Python to import the files. *Required new file*
* `lib/ansible/modules/$area/$prefix/$yourfirstmodule.py` - A single module. *Required new file*
* `lib/ansible/utils/module_docs_fragments/$prefix.py` - Code documentation, such as details regarding common arguments. *Optional new file*
* `lib/ansible/module_utils/$prefix.py` - Code shared between more than one module, such as common arguments. *Optional new file*
*  `docs/docsite/rst/dev_guide/developing_module_utilities.rst` - Document your new `module_utils` file. *Optional update to existing file*

And that's it.

Before pushing your PR to GitHub it's a good idea to review the :doc:`developing_modules_checklist` again

After (pushing and publishing your PR on https://github.com/ansible/ansible a Shippable CI test should run (generally within a few minutes), check the results (at the end of the PR page) and ensure it's passing (green), if not inspect each of the results. Most of the errors should be self explanitory and are generally related to badly formatted documentation (FIXME yamlonline validator) or code that isn't valid Python 2.4 & Python 2.6 (FIXME porting page). If you aren't sure what a Shippable test message means copy it into the PR and add as a comment and we will review.

If you need further advice join the `#ansible-devel` IRC channel (details in "Where to get support")


Please don't force push your PRs, we prefer individual commits in the same PR, the PR will be squashed and merged by the Ansible Core Team when it's ready to be accepted. This is required to allow reviews to see what's changed since they started looking at your PR.

We have a "ansibot" helper that comments on GitHub Issues and PRs which should highlight important information.




Subsiquent PRs
``````````````````````

Then one module per PR
* Why

Finally
````````````````````````````
Ansibullbot
Once your module is accepted, you become responsible for maintenance of that module, which means responding to pull requests and issues in a reasonably timely manner.

CHANEGLOG.md


.. seealso::

# FIXME
   `irc.freenode.net <http://irc.freenode.net>`_
       #ansible-devel IRC chat channel


# FIXME: Fix heading levels (Before you start, (sub, sub), Your first PR
# FIXME: Link from developing_modules.rst
# FIXME: Review all links
# FIXME: Review all anchors
# FIXME: What's a better filename and title for this page?
# NOTE:  Do we want to guide partners into the standard community work flow? (How can we title/aim this page so it does that)
# FIXME: Review all my "Network Partner" emails
# FIXME: Do we want to put anything about submission dates, or will that come from the Ansible member of staff looking after the relationship?
# FIXME: Note about forking & creating a separate branch?
