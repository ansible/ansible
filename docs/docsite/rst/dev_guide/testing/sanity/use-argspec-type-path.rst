use-argspec-type-path
=====================

The AnsibleModule argument_spec knows of several types beyond the standard python types.  One of
these is ``path``.  When used, type ``path`` ensures that an argument is a string and expands any
shell variables and tilde characters.

This test looks for use of :func:`os.path.expanduser <python:os.path.expanduser>` in modules.  When found, it tells the user to
replace it with ``type='path'`` in the module's argument_spec or list it as a false positive in the
test.
