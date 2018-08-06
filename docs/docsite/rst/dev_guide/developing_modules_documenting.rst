.. _module_documenting:

Module Formatting and Documentation
===================================

Every module should begin with a shebang (``#! /usr/bin/python`` or the equivalent if you're developing in another language), followed by the following six sections in this order:

1. :ref:`Copyright and License <copyright>`
2. :ref:`ANSIBLE_METADATA <ansible_metadata_block>`
3. :ref:`DOCUMENTATION <documentation_block>`
4. :ref:`EXAMPLES <examples_block>`
5. :ref:`RETURN <return_block>`
6. :ref:`Python imports <python_imports>`


.. note:: Why don't the imports go first?

  Keen Python programmers may notice that contrary to PEP 8's advice we don't put ``imports`` at the top of the file. This is because the ``ANSIBLE_METADATA`` through ``RETURN`` sections are not used by the module code itself; they are essentially extra docstrings for the file. The imports are placed after these special variables for the same reason as PEP 8 puts the imports after the introductory comments and docstrings. This keeps the active parts of the code together and the pieces which are purely informational apart. The decision to exclude E402 is based on readability (which is what PEP 8 is about). Documentation strings in a module are much more similar to module level docstrings, than code, and are never utilized by the module itself. Placing the imports below this documentation and closer to the code, consolidates and groups all related code in a congruent manner to improve readability, debugging and understanding.

.. warning:: **Copy old modules with care!**

  Some older modules in Ansible Core have ``imports`` at the bottom of the file, ``Copyright`` notices with the full GPL prefix, and/or ``ANSIBLE_METADATA`` fields in the wrong order. These are legacy idioms that need updating - do not copy them into new modules. Over time we're updating and correcting older modules. Please follow the guidelines on this page!

.. _copyright:

Copyright and License
----------------------

After the shebang, there should be a `copyright line <https://www.gnu.org/licenses/gpl-howto.en.html>`_ with the original copyright holder and a license declaration. The license declaration should be ONLY one line, not the full GPL prefix.:

.. code-block:: python

    #!/usr/bin/python
    
    # Copyright: (c) 2018, Terry Jones <terry.jones@example.org>
    # GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

Major additions to the module (for instance, rewrites) may add additional copyright lines. Any legal review will include the source control history, so an exhaustive copyright header is not necessary. When adding a second copyright line for a significant feature or rewrite, add the newer line above the older one:

.. code-block:: python

    #!/usr/bin/python
    
    # Copyright: (c) 2017, [New Contributor(s)]
    # Copyright: (c) 2015, [Original Contributor(s)]
    # GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

.. _ansible_metadata_block:

ANSIBLE_METADATA Block
----------------------

``ANSIBLE_METADATA`` contains information about the module for use by other tools. For new modules, the following block can be simply added into your module

.. code-block:: python

   ANSIBLE_METADATA = {'metadata_version': '1.1',
                       'status': ['preview'],
                       'supported_by': 'community'}

.. warning::

   * ``metadata_version`` is the version of the ``ANSIBLE_METADATA`` schema, *not* the version of the module.
   * Promoting a module's ``status`` or ``supported_by`` status should only be done by members of the Ansible Core Team.

Fields
^^^^^^

:metadata_version: An "X.Y" formatted string. X and Y are integers which
   define the metadata format version. Modules shipped with Ansible are
   tied to an Ansible release, so we will only ship with a single version
   of the metadata. We'll increment Y if we add fields or legal values
   to an existing field. We'll increment X if we remove fields or values
   or change the type or meaning of a field.
   Current metadata_version is "1.1"

:supported_by: Who supports the module.
   Default value is ``community``. For information on what the support level values entail, please see
   :ref:`Modules Support <modules_support>`. Values are:

   * core
   * network
   * certified
   * community
   * curated (*deprecated value - modules in this category should be core or
     certified instead*)

:status: List of strings describing how stable the module is likely to be.
   The default value is a single element list ["preview"]. The following strings are valid
   statuses and have the following meanings:

   :stableinterface: The module's parameters are stable. Every effort will be made not to remove parameters or change
      their meaning. **Not** a rating of the module's code quality.
   :preview: The module is in tech preview. It may be
      unstable, the parameters may change, or it may require libraries or
      web services that are themselves subject to incompatible changes.
   :deprecated: The module is deprecated and will be removed in a future release.
   :removed: The module is not present in the release. A stub is
      kept so that documentation can be built. The documentation helps
      users port from the removed module to new modules.

.. _documentation_block:

DOCUMENTATION Block
-------------------

Ansible's online module documentation is generated from the ``DOCUMENTATION`` blocks at the beginning of each module's source code. The ``DOCUMENTATION`` block must be valid YAML. You may find it easier to start writing your ``DOCUMENTATION`` string in an :ref:`editor with YAML syntax highlighting <other_tools_and_programs>` before you include it in your Python file. See an example documentation string at `examples/DOCUMENTATION.yml <https://github.com/ansible/ansible/blob/devel/examples/DOCUMENTATION.yml>`_.

Include it in your module file like this:

.. code-block:: python

    #!/usr/bin/python
    # Copyright (c) 2017 [REPLACE THIS]
    # GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

    DOCUMENTATION = '''
    ---
    module: modulename
    short_description: This is a sentence describing the module
    # ... snip ...
    '''

Fields
^^^^^^

All fields are lower-case. All fields are required unless specified otherwise:

:module:
  The name of the module. This must be the same as the filename, without the ``.py`` extension.
:short_description:
  * A short description which is displayed on the :ref:`all_modules` page and ``ansible-doc -l``.
  * The ``short_description`` is displayed by ``ansible-doc -l`` without any category grouping, so it needs enough detail to explain the module's purpose without the context of the directory structure in which it lives.
  * Unlike ``description:``, ``short_description`` should not have a trailing period/full stop.
:description:
  * A detailed description (generally two or more sentences).
  * Must be written in full sentences, i.e. with capital letters and periods/full stops.
  * Shouldn't mention the module name.
:version_added:
  * The version of Ansible when the module was added.
  * This is a string, and not a float, i.e. ``version_added: "2.1"``
:author:
  Name of the module author in the form ``First Last (@GitHubID)``. Use a multi-line list if there is more than one author.
:deprecated:
  Not Required. When you deprecate a module you must:

  * Mention the deprecation in the relevant ``CHANGELOG``
  * Reference the deprecation in the relevant ``porting_guide_x.y.rst``
  * Rename the file so it starts with an ``_``
  * Update ``ANSIBLE_METADATA`` to contain ``status: ['deprecated']``
  * Set the following values in the documentation:

  :removed_in: A `string`, such as ``"2.9"``, which represents the version of Ansible this module will replaced with docs only module stub.
  :why: Optional string that used to detail why this has been removed.
  :alternative: Inform users they should do instead, i.e. ``Use M(whatmoduletouseinstead) instead.``.

:options:
  Not Required. If the module has no options (for example, it's a ``_facts`` module), you can use ``options: {}``. If your module has options (in other words, accepts arguments), each option should be documented thoroughly. For each module argument, include:

  :option-name:

    * Declarative operation (not CRUD), to focus on the final state, for example `online:`, rather than `is_online:`.
    * The name of the option should be consistent with the rest of the module, as well as other modules in the same category.

  :description:

    * Detailed explanation of what this option does. It should be written in full sentences.
    * Should not list the possible values (that's what ``choices:`` is for, though it should explain `what` the values do if they aren't obvious).
    * If an optional parameter is sometimes required this need to be reflected in the documentation, e.g. "Required when I(state=present)."
    * Mutually exclusive options must be documented as the final sentence on each of the options.
  :required:
    Only needed if ``true``, otherwise we assume the option is not required.
  :default:

    * If `required` is false/missing, `default` may be specified (assumed 'null' if missing).
    * Ensure that the default parameter in the docs matches the default parameter in the code.
    * The default option must not be listed as part of the description.
    * If the option is a boolean value, you can use any of the boolean values recognized by Ansible:
      (such as true/false or yes/no).  Choose the one that reads better in the context of the option.
  :choices:
    List of option values. Should be absent if empty.
  :type:

    * Specifies the data type that option accepts, must match the ``argspec``.
    * If an argument is ``type='bool'``, this field should be set to ``type: bool`` and no ``choices`` should be specified.
  :aliases:
    List of option name aliases; generally not needed.
  :version_added:
    Only needed if this option was extended after initial Ansible release, i.e. this is greater than the top level `version_added` field.
    This is a string, and not a float, i.e. ``version_added: "2.3"``.
  :suboptions:
    If this option takes a dict, you can define it here. See `azure_rm_securitygroup`, `os_ironic_node` for examples.
:requirements:
  List of requirements, and minimum versions (if applicable).
:notes:
    Details of any important information that doesn't fit in one of the above sections; for example if ``check_mode`` isn't supported, or a link to external documentation.

.. _examples_block:

EXAMPLES block
--------------

Examples should demonstrate real-world usage in multi-line plain-text YAML format. The best examples are ready for the user to 
copy and paste into a playbook. Review and update your examples with every change to your module.

Per playbook best practices, each example should include a `name:` line.

``EXAMPLES`` string within the module like this::

    EXAMPLES = '''
    - name: Ensure foo is installed
      modulename:
        name: foo
        state: present
    '''

If the module returns facts that are often needed, an example of how to use them can be helpful.

.. _return_block:

RETURN Block
------------

The RETURN section documents what the module returns. If your module doesn't return anything (apart from the standard returns), this section of your documentation should read::

   ``RETURN = ''' # '''``

Otherwise, for each value returned, provide the following fields. All fields are required unless specified otherwise.

:return name:
  Name of the returned field.

  :description:
    Detailed description of what this value represents.
  :returned:
    When this value is returned, such as ``always``, or ``on success``
  :type:
    Data type
  :sample:
    One or more examples.
  :version_added:
    Only needed if this return was extended after initial Ansible release, i.e. this is greater than the top level `version_added` field.
    This is a string, and not a float, i.e. ``version_added: "2.3"``.
  :contains:
    Optional, if you set `type: complex` you can detail the dictionary here by repeating the above elements.

    :return name:
      One per return

      :description:
        Detailed description of what this value represents.
      :returned:
        When this value is returned, such as `always`, on `success`, `always`
      :type:
        Data type
      :sample:
        One or more examples.
      :version_added:
        Only needed if this return was extended after initial Ansible release, i.e. this is greater than the top level `version_added` field.
        This is a string, and not a float, i.e. ``version_added: "2.3"``.


For complex nested returns type can be specified as ``type: complex``. For example::


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
    '''

    RETURN = '''
    packages:
        description: Information about package requirements
        returned: On success
        type: complex
        contains:
            missing:
                description: Packages that are missing from the system
                returned: success
                type: list
                sample:
                    - libmysqlclient-dev
                    - libxml2-dev
            badversion:
                description: Packages that are installed but at bad versions.
                returned: success
                type: list
                sample:
                    - package: libxml2-dev
                      version: 2.9.4+dfsg1-2
                      constraint: ">= 3.0"
    '''


Linking within the ``DOCUMENTATION`` block
------------------------------------------

You can link from your module documentation to other module docs, other resources on docs.ansible.com, and resources elsewhere on the internet. The correct formats for these links are:

* ``L()`` for Links with a heading
* ``U()`` for URLs
* ``I()`` for option names
* ``C()`` for files and option values
* ``M()`` for module names

Example usage::

    Or if not set the environment variable C(ACME_PASSWORD) will be used.
    ...
    Required if I(state=present)
    ...
    Mutually exclusive with I(project_src) and I(files).
    ...
    See also M(win_copy) or M(win_template).
    ...
    Time zone names are from the L(tz database,https://en.wikipedia.org/wiki/List_of_tz_database_time_zones)
    See U(https://www.ansible.com/products/tower) for an overview.
    ...
    See L(IOS Platform Options guide, ../network/user_guide/platform_ios.html)


.. note::

  If you wish to refer a collection of modules, use ``C(..)``, e.g. ``Refer to the C(win_*) modules.``

Documentation fragments
-----------------------

Some categories of modules share common documentation, such as details on how to authenticate options, or file mode settings. Rather than duplicate that information it can be shared using ``docs_fragments``.

These shared fragments are similar to the standard documentation block used in a module, they are just contained in a ``ModuleDocFragment`` class.

All the existing ``docs_fragments`` can be found in ``lib/ansible/utils/module_docs_fragments/``.

To include, simply add in ``extends_documentation_fragment: FRAGMENT_NAME`` into your module.

Examples can be found by searching for ``extends_documentation_fragment`` under the Ansible source tree.

Testing documentation
---------------------

The simplest way to check if your documentation works is to use ``ansible-doc`` to view it. Any parsing errors will be apparent, and details can be obtained by adding ``-vvv``.

If you are going to submit the module for inclusion in the main Ansible repo you should make sure that it renders correctly as HTML.
Put your completed module file into the ``lib/ansible/modules/$CATEGORY/`` directory and then
run the command: ``make webdocs``. The new 'modules.html' file will be
built in the ``docs/docsite/_build/html/$MODULENAME_module.html`` directory.

In order to speed up the build process, you can limit the documentation build to
only include modules you specify, or no modules at all. To do this, run the command:
``MODULES=$MODULENAME make webdocs``. The ``MODULES`` environment variable
accepts a comma-separated list of module names. To skip building
documentation for all modules, specify a non-existent module name, for example:
``MODULES=none make webdocs``.

You may also build a single page of the entire docsite. From ``ansible/docs/docsite`` run ``make htmlsingle rst=[relative path to the .rst file]``, for example: ``make htmlsingle rst=dev_guide/developing_modules_documenting.rst``

To test your documentation against your ``argument_spec`` you can use ``validate-modules``. Note that this option isn't currently enabled in Shippable due to the time it takes to run.

.. code-block:: bash

   # If you don't already, ensure you are using your local checkout
   source hacking/env-setup
   ./test/sanity/validate-modules/validate-modules --arg-spec --warnings  lib/ansible/modules/your/modules/

.. tip::

   If you're having a problem with the syntax of your YAML you can
   validate it on the `YAML Lint <http://www.yamllint.com/>`_ website.

For more information in testing, including how to add unit and integration tests, see :doc:`testing`.

.. _python_imports:

Python Imports
--------------

Starting with Ansible version 2.2, all new modules are required to use imports in the form:

.. code-block:: python

   from module_utils.basic import AnsibleModule


.. warning::

   The use of "wildcard" imports such as ``from module_utils.basic import *`` is no longer allowed.

