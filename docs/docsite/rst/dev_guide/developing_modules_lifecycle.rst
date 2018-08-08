
Deprecating and making module aliases
======================================

Starting in 1.8, you can deprecate modules by renaming them with a preceding ``_``, i.e. ``old_cloud.py`` to
``_old_cloud.py``. This keeps the module available, but hides it from the primary docs and listing.

When deprecating a module:

1) Set the ``ANSIBLE_METADATA`` `status` to `deprecated`.
2) In the ``DOCUMENTATION`` section, add a `deprecated` field along the lines of::

    deprecated: Deprecated in 2.3. Use M(whatmoduletouseinstead) instead.

3) Add the deprecation to CHANGELOG.md under the ``###Deprecations:`` section.

Alias module names
------------------

You can also rename modules and keep an alias to the old name by using a symlink that starts with _.
This example allows the stat module to be called with fileinfo, making the following examples equivalent::

    EXAMPLES = '''
    ln -s stat.py _fileinfo.py
    ansible -m stat -a "path=/tmp" localhost
    ansible -m fileinfo -a "path=/tmp" localhost
    '''
