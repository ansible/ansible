.. _module_documenting:

Documenting Your Module
```````````````````````

The online module documentation is generated from the modules themselves.
Therefor all modules included with Ansible must have a
``DOCUMENTATION`` string. This string must be a valid YAML document
which conforms to the schema defined below. You may find it easier to
start writing your ``DOCUMENTATION`` string in an editor with YAML
syntax highlighting before you include it in your Python file.


DOCUMENTATION Block
'''''''''''''''''''

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


The following fields can be used and are all required unless specified otherwise

* ``module:``
  The name of the module, same as the file without `.py`.
* ``short_description:``

  * Displayed on the :doc:`../list_of_all_modules` page and ``ansible-doc -l``.
  * Must have enough detail without the context of the category.
  * Without a trailing full stop
* ``description:``
  * A longer description than `short_description`, which goes into more detail, generally two or more sentences.
  * Must be written in full sentences, i.e. with capital letters and fullstops.
  * Shouldn't mention the name module.
* ``version_added:``
  The version of Ansible when the module was added.
  This is a `string`, and not a float, i.e. ``version_added: "2.1"``
* ``author:``
  In the form ``First Last (@GitHubID)``, use a multi-line list if there is more than one.
* ``options:``
  One per module argument

  * ``description:``

    * Detailed explanation of what this option does and what it does. Written in full sentences.
    * Should not list the options (that's what ``choices:`` is for, though it should explain `what` the values do if they aren't obvious.
    * If an argument takes both True)/False and Yes)/No, the documentation should use True and False.
    * If an optional parameter is sometimes required this need to be reflected in the documentation, e.g. "Required when C(state=present)."
    * Mutually exclusive options must be documented as the final sentence on each of the options.
  * ``required:``
    Only needed if true, otherwise it is assumed to be false.
  * ``default:``
    * If `required` is false/missing, `default` may be specified (assumed 'null' if missing).
    * Ensure that the default parameter in docs matches default parameter in code. The default option must not be listed as part of the description.
  * ```choices``
    Should be absent if empty.
  * ``aliases:``
    Should be absent if empty.
  * ``version_added:``
    Only needed if this option was extended after initial Ansible release, i.e. this is greater than the top level `version_added` field.
    This is a string, and not a float, i.e. `version_added: "2.3"`
* ``requirements:``
    List of requirements, and minimum versions (if applicable)
* ``notes:``
    Details of any important information that doesn't fit in one of the above sections, for example if ``check_mode`` isn't supported, or a link to external documentation.




EXAMPLES block
''''''''''''''

The EXAMPLES section, just like the documentation section, it is required for all new modules.

Examples should demonstrate real world usage, and be written in multi-line YAML format in plain text in.

Ensure that examples are kept in sync with the options during the PR review and any following code refactor.

As per playbook best practice a `name:` should be specified.

``EXAMPLES`` string within the module like this::

    EXAMPLES = '''
    - name: Ensure foo is installed
      modulename:
        name: foo
        state: present
    '''

If the module returns facts that are often needed an example of how to use them can be helpful.


RETURN Block
''''''''''''

The RETURN section documents what the module returns, it is required for all new modules.

For each value returned, provide a ``description``, in what circumstances the value is ``returned``,
the ``type`` of the value and a ``sample``.  For example, from the ``copy`` module::

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

Formatting options
''''''''''''''''''
These formatting functions are ``U()``, ``M()``, ``I()``, and ``C()``
for URL, link to help for another module, `italic`, and ``constant-width`` respectively. It is suggested
to use ``C()`` for file and option names, and ``I()`` when referencing
parameters; module names should be specified as ``M(module)`` to create a
link to the online documentation for that module.


Example usage::

    Or if not set the environment variable C(ACME_PASSWORD) will be used.
    ...
    Required if I(state=present)
    ...
    Mutually exclusive with C(project_src) and C(files).
    ...
    See also M(win_copy) or M(win_template).
    ...
    See U(https://www.ansible.com/tower) for an overview.


.. note::

  If you wish to refer a collection of modules use ``C(..)``, e.g. ``Refer to the C(win_*) modules.``

Documentation fragments
```````````````````````

Some categories of modules share common documentation, such as details on how to authenticate options, or file mode settings. Rather than duplicate that information it be shared using ``docs_fragments``.

These shared fragments are similar to the standard documentation block used in a module, they are just contained in a ``ModuleDocFragment`` class.

All the existing ``docs_fragments`` can be found in ``lib/ansible/utils/module_docs_fragments/``.

To include simply add in ``extends_documentation_fragment: FRAGMENT_NAME`` into your module.

Examples can be found by searching for ``extends_documentation_fragment`` under the Ansible source tree.

Testing documentation
'''''''''''''''''''''

Put your completed module file into the ``lib/ansible/modules/$CATEGORY/`` directory and then
run the command: ``make webdocs``. The new 'modules.html' file will be
built and built as ``docs/docsite/_build/html/$MODULENAME_module.html`` directory.

.. tip::

   If you're having a problem with the syntax of your YAML you can
   validate it on the `YAML Lint <http://www.yamllint.com/>`_ website.
