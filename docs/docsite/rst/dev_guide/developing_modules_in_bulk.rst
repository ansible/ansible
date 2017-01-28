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
* Understand that all modules shipped with Ansible MUST be done so under the GPLv3 license. Files under the `lib/ansible/module_utils/` directory must be under the FIXME license.
* Have a look at the existing modules, especially in the same functional area (such as cloud, networking, databases) in the :doc:`../list_of_all_modules` for a list of existing modules and how they've been named.


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
FIXME: I (gundalow) isn't sure if we want to preasure the Public Core Meetings with this, though that is one recomended way for the community to reach the Core Team.

Where to get support
````````````````````
Ansible has a very strong community, and we trust you are module developers will help grow.

The community is a great pool of resource and knowledge.
# FIXME Links to page that has community info in

Subscribe to (at least) announce and devel. This is so you will be aware of deadlines regarding codefreeze in the lead upto releases and other important information

We have found that IRC `#ansible-devel` works best for module developers do to giving an interactive dialogue.
Code and questions can be put into pastebin/gist.github.com, then you can reference that URL in chat.


First PR
`````````

What should be in it
Explain what each file is for
What should not be included, e.g. readme
Once available review the Shippable results (if failing/red). Shippable is part of our CI (Continious Integration) process and has a number of checks you must ensure are passing (green)
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

   :doc:`../modules`
       Learn about available modules
   :doc:`developing_plugins`
       Learn about developing plugins
   :doc:`developing_api`
       Learn about the Python API for playbook and task execution
   `GitHub modules directory <https://github.com/ansible/ansible/tree/devel/lib/ansible/modules>`_
       Browse module source code
   `Mailing List <http://groups.google.com/group/ansible-devel>`_
       Development mailing list
   `irc.freenode.net <http://irc.freenode.net>`_
       #ansible-devel IRC chat channel



# FIXME: Link from developing_modules.rst
# FIXME: Review all links
# FIXME: Review all anchors
# FIXME: What's a better filename and title for this page?
# NOTE:  Do we want to guide partners into the standard community work flow? (How can we title/aim this page so it does that)
# FIXME: Review all my "Network Partner" emails
# FIXME: Do we want to put anything about submission dates, or will that come from the Ansible member of staff looking after the relationship?
