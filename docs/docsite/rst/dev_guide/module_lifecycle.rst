.. _module_lifecycle:

**********************************
The lifecycle of an Ansible module
**********************************

Modules in the main Ansible repo have a defined life cycle, from first introduction to final removal. The module life cycle is tied to the `Ansible release cycle <release_cycle>`.
A module may move through these four states:

1. When a module is first accepted into Ansible, we consider it in tech preview and will mark it as such in the documentation.

2. If a module matures, we will remove the 'preview' mark in the documentation. We support (though we cannot guarantee) backwards compatibility for these modules, which means their parameters should be maintained with stable meanings.

3. If a module's target API changes radically, or if someone creates a better implementation of its functionality, we may mark it deprecated. Modules that are deprecated are still available but they are reaching the end of their life cycle. We retain deprecated modules for 4 release cycles with deprecation warnings to help users update playbooks and roles that use them.

4. When a module has been deprecated for four release cycles, we remove the code and mark the stub file removed. Modules that are removed are no longer shipped with Ansible. The stub file helps users find alternative modules.

.. _deprecating_modules:

Deprecating modules
===================

To deprecate a module, you must:

1. Rename the file so it starts with an ``_``, for example, rename ``old_cloud.py`` to ``_old_cloud.py``. This keeps the module available and marks it as deprecated on the module index pages.
2. Mention the deprecation in the relevant ``CHANGELOG``.
3. Reference the deprecation in the relevant ``porting_guide_x.y.rst``.
4. Add ``deprecated:`` to the documentation with the following sub-values:

  :removed_in: A ``string``, such as ``"2.10"``; the version of Ansible where the module will be replaced with a docs-only module stub. Usually current release +4. Mutually exclusive with :removed_by_date:.
  :remove_by_date: (Added in Ansible 2.10). An ISO 8601 formatted date when the module will be removed. Usually 2 years from the date the module is deprecated. Mutually exclusive with :removed_in:.
  :why: Optional string that used to detail why this has been removed.
  :alternative: Inform users they should do instead, for example, ``Use M(whatmoduletouseinstead) instead.``.

* note: with the advent of collections and ``routing.yml`` we might soon require another entry in this file to mark the deprecation.

* For an example of documenting deprecation, see this `PR that deprecates multiple modules <https://github.com/ansible/ansible/pull/43781/files>`_.
  Some of the elements in the PR might now be out of date.

Changing a module name
======================

You can also rename a module and keep an alias to the old name by using a symlink that starts with _.
This example allows the ``stat`` module to be called with ``fileinfo``, making the following examples equivalent::

    EXAMPLES = '''
    ln -s stat.py _fileinfo.py
    ansible -m stat -a "path=/tmp" localhost
    ansible -m fileinfo -a "path=/tmp" localhost
    '''
