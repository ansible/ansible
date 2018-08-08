.. _module_lifecycle:

The lifecycle of an Ansible module
======================================

Include information on all status values: preview, stableinterface, deprecated, and removed.

Deprecating modules
^^^^^^^^^^^^^^^^^^^

Starting in 1.8, you can deprecate modules by renaming them with a preceding ``_``, i.e. ``old_cloud.py`` to
``_old_cloud.py``. This keeps the module available, but hides it from the primary docs and listing.

When deprecating a module:

1) Set the ``ANSIBLE_METADATA`` `status` to `deprecated`.
2) In the ``DOCUMENTATION`` section, add a `deprecated` field along the lines of::

    deprecated: Deprecated in 2.3. Use M(whatmoduletouseinstead) instead.

3) Add the deprecation to CHANGELOG.md under the ``###Deprecations:`` section.

* When you deprecate a module you must:

  * Mention the deprecation in the relevant ``CHANGELOG``
  * Reference the deprecation in the relevant ``porting_guide_x.y.rst``
  * Rename the file so it starts with an ``_``
  * Update ``ANSIBLE_METADATA`` to contain ``status: ['deprecated']``
  * Add ``deprecated:`` to the documentation with the following sub-values:
  :removed_in: A `string`, such as ``"2.9"``, which represents the version of Ansible this module will replaced with docs only module stub.
  :why: Optional string that used to detail why this has been removed.
  :alternative: Inform users they should do instead, i.e. ``Use M(whatmoduletouseinstead) instead.``.

* See the `kubernetes module code <https://github.com/ansible/ansible/blob/devel/lib/ansible/modules/clustering/k8s/_kubernetes.py>`_
  for an example of documenting deprecation.



Alias module names
------------------

You can also rename modules and keep an alias to the old name by using a symlink that starts with _.
This example allows the stat module to be called with fileinfo, making the following examples equivalent::

    EXAMPLES = '''
    ln -s stat.py _fileinfo.py
    ansible -m stat -a "path=/tmp" localhost
    ansible -m fileinfo -a "path=/tmp" localhost
    '''
