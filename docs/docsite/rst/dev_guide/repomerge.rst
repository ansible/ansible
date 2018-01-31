==========
Repo Merge
==========

Background
----------
On Tuesday 6th December 2016, the Ansible Core Team re-merged the module repositories back into `ansible/ansible <https://github.com/ansible/ansible/>`_ in GitHub. The two module repos will be essentially locked, though they will be kept in place for the existing 2.1 and 2.2 dependencies. Once 2.2 moves out of official support (early 2018), these repositories will be fully readonly for all branches. Until then, any issues/PRs opened there will be auto-closed with a note to open it on `ansible/ansible <https://github.com/ansible/ansible/>`_.

Why Are We Doing This (Again...)?
-----------------------------------

For those who've been using Ansible long enough, you know that originally we started with a single repository. The original intention of the core vs. extras split was that core would be better supported/tested/etc. Extras would have been a bit more of a "wild-west" for modules, to allow new modules to make it into the distribution more quickly. Unfortunately this never really worked out, as well as the following:

1. Many modules in the core repo were also essentially "grand-fathered" in, despite not having a good set of tests or dedicated maintainers from the community.
2. The time in queue for modules to be merged into extras was not really any different from the time to merge modules into core.
3. The split introduced a few other problems for contributors such as having to submit multiple related PRs for modules with tests, or for those which rely on action plugins. 
4. git submodules are notoriously complicated, even for contributors with decent git experience. The constant need to update git submodule pointers for devel and each stable branch can lead to testing surprises and really buys us nothing in terms of flexibility.
5. Users can already be confused about where to open issues, especially when the problem appears to be with a module but is actually an action plugin (ie. template) or something more fundamental like includes. Having everything back in one repo makes it easier to link issues, and you're always sure to open a bug report in the right place.

Metadata - Support/Ownership and Module Status
----------------------------------------------------------------------

As part of this move, we will be introducing module metadata, which will contain a couple of pieces of information regarding modules:

1. Support Status: This field indicates who supports the module, whether it's the core team, the community, the person who wrote it, or if it is an abandoned module which is not receiving regular updates. The Ansible team has gone through the list of modules and we have marked about 100 of them as "Core Supported", meaning a member of the Ansible core team should be actively fixing bugs on those modules. The vast majority of the rest will be community supported. This is not really a change from the status quo, this just makes it clearer.
2. Module Status: This field indicates how well supported that module may be. This generally applies to the maturity of the module's parameters, however, not necessarily its bug status.


The documentation pages for modules will be updated to reflect the above information as well, so that users can evaluate the status of a module before committing to using it in playbooks and roles.
