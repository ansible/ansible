.. _module_documenting:

Documenting Your Module
```````````````````````

All modules included in the CORE distribution must have a
``DOCUMENTATION`` string. This string MUST be a valid YAML document
which conforms to the schema defined below. You may find it easier to
start writing your ``DOCUMENTATION`` string in an editor with YAML
syntax highlighting before you include it in your Python file.


Example
'''''''

See an example documentation string in the checkout under `examples/DOCUMENTATION.yml <https://github.com/ansible/ansible/blob/devel/examples/DOCUMENTATION.yml>`_.

Include it in your module file like this:

.. code-block:: python

    #!/usr/bin/python
    # Copyright header....

    DOCUMENTATION = '''
    ---
    module: modulename
    short_description: This is a sentence describing the module
    # ... snip ...
    '''

The ``description``, and ``notes`` fields
support formatting with some special macros.

These formatting functions are ``U()``, ``M()``, ``I()``, and ``C()``
for URL, module, italic, and constant-width respectively. It is suggested
to use ``C()`` for file and option names, and ``I()`` when referencing
parameters; module names should be specified as ``M(module)``.

Examples should be written in YAML format in plain text in an
``EXAMPLES`` string within the module like this::

    EXAMPLES = '''
    - modulename:
        opt1: arg1
        opt2: arg2
    '''

The EXAMPLES section, just like the documentation section, is required in
all module pull requests for new modules.

The RETURN section documents what the module returns. For each value returned,
provide a ``description``, in what circumstances the value is ``returned``,
the ``type`` of the value and a ``sample``.  For example, from
the ``copy`` module::

    RETURN = '''
    dest:
        description: destination file/path
        returned: success
        type: string
        sample: /path/to/file.txt
    src:
        description: source file used for the copy on the target machine
        returned: changed
        type: string
        sample: /home/httpd/.ansible/tmp/ansible-tmp-1423796390.97-147729857856000/source
    md5sum:
        description: md5 checksum of the file after running copy
        returned: when supported
        type: string
        sample: 2a5aeecc61dc98c4d780b14b330e3282
    ...
    '''

Building & Testing
''''''''''''''''''

Put your completed module file into the 'library' directory and then
run the command: ``make webdocs``. The new 'modules.html' file will be
built and appear in the 'docsite/' directory.

.. tip::

   If you're having a problem with the syntax of your YAML you can
   validate it on the `YAML Lint <http://www.yamllint.com/>`_ website.

.. tip::

    You can set the environment variable ANSIBLE_KEEP_REMOTE_FILES=1 on the controlling host to prevent ansible from
    deleting the remote files so you can debug your module.
