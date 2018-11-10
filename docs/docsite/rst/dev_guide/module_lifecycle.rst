.. _module_lifecycle:

**********************************
The lifecycle of an Ansible module
**********************************

Modules in the main Ansible repo have a defined life cycle, from first introduction to final removal. The module life cycle is tied to the `Ansible release cycle <release_cycle>` and reflected in the :ref:`ansible_metadata_block`. A module may move through these four states:

1. When a module is first accepted into Ansible, we consider it in tech preview and mark it ``preview``. Modules in ``preview`` are not stable. You may change the parameters or dependencies, expand or reduce the functionality of ``preview`` modules. Many modules remain ``preview`` for years.

2. If a module matures, we may mark it ``stableinterface`` and commit to maintaining its parameters, dependencies, and functionality. We support (though we cannot guarantee) backwards compatibility for ``stableinterface`` modules, which means their parameters should be maintained with stable meanings.

3. If a module's target API changes radically, or if someone creates a better implementation of its functionality, we may mark it ``deprecated``. Modules that are ``deprecated`` are still available but they are reaching the end of their life cycle. We retain deprecated modules for 4 release cycles with deprecation warnings to help users update playbooks and roles that use them.

4. When a module has been deprecated for four release cycles, we remove the code and mark the stub file ``removed``. Modules that are ``removed`` are no longer shipped with Ansible. The stub file helps users find alternative modules.

.. _deprecating_modules:

Deprecating modules
===================

To deprecate a module, you must:

1. Rename the file so it starts with an ``_``, for example, rename ``old_cloud.py`` to ``_old_cloud.py``. This keeps the module available and marks it as deprecated on the module index pages.
2. Mention the deprecation in the relevant ``CHANGELOG``.
3. Reference the deprecation in the relevant ``porting_guide_x.y.rst``.
4. Update ``ANSIBLE_METADATA`` to contain ``status: ['deprecated']``.
5. Add ``deprecated:`` to the documentation with the following sub-values:

  :removed_in: A ``string``, such as ``"2.9"``; the version of Ansible where the module will be replaced with a docs-only module stub. Usually current release +4.
  :why: Optional string that used to detail why this has been removed.
  :alternative: Inform users they should do instead, i.e. ``Use M(whatmoduletouseinstead) instead.``.

* For an example of documenting deprecation, see this `PR that deprecates multiple modules <https://github.com/ansible/ansible/pull/43781/files>`_.

Changing a module name
======================

You can also rename a module and keep an alias to the old name by using a symlink that starts with _.
This example allows the ``stat`` module to be called with ``fileinfo``, making the following examples equivalent::

    EXAMPLES = '''
    ln -s stat.py _fileinfo.py
    ansible -m stat -a "path=/tmp" localhost
    ansible -m fileinfo -a "path=/tmp" localhost
    '''
