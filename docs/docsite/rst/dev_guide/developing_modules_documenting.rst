.. _module_documenting:

Documenting Your Module
=======================

.. contents:: Topics

The online module documentation is generated from the modules themselves.
As the module documentation is generated from documentation strings contained in the modules, all modules included with Ansible must have a ``DOCUMENTATION`` string.
This string must be a valid YAML document
which conforms to the schema defined below. You may find it easier to
start writing your ``DOCUMENTATION`` string in an editor with YAML
syntax highlighting before you include it in your Python file.

All modules must have the following sections defined in this order:

1. Copyright
2. ANSIBLE_METADATA
3. DOCUMENTATION
4. EXAMPLES
5. RETURN
6. Python imports

.. note:: Why don't the imports go first?

  Keen Python programmers may notice that contrary to PEP 8's advice we don't put ``imports`` at the top of the file. This is because the ``ANSIBLE_METADATA`` through ``RETURN`` sections are not used by the module code itself; they are essentially extra docstrings for the file. The imports are placed after these special variables for the same reason as PEP 8 puts the imports after the introductory comments and docstrings. This keeps the active parts of the code together and the pieces which are purely informational apart. The decision to exclude E402 is based on readability (which is what PEP 8 is about). Documentation strings in a module are much more similar to module level docstrings, than code, and are never utilized by the module itself. Placing the imports below this documentation and closer to the code, consolidates and groups all related code in a congruent manner to improve readability, debugging and understanding.

.. warning:: Why do some modules have imports at the bottom of the file?

  If you look at some existing older modules, you may find imports at the bottom of the file. Do not copy that idiom into new modules as it is a historical oddity due to how modules used to be combined with libraries. Over time we're moving the imports to be in their proper place.


.. _copyright:

Copyright
----------------------

The beginning of every module should look about the same. After the shebang,
there should be at least two lines covering copyright and licensing of the
code.

.. code-block:: python

    #!/usr/bin/python
    
    # Copyright: (c) 2018, Terry Jones <terry.jones@example.org>
    # GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

Every file should have a copyright line (see `The copyright notice <https://www.gnu.org/licenses/gpl-howto.en.html>`_)
with the original copyright holder. Major additions to the module (for
instance, rewrites) may add additional copyright lines. Any legal questions
need to review the source control history, so an exhaustive copyright header is
not necessary.

The license declaration should be ONLY one line, not the full GPL prefix. If
you notice a module with the full prefix, feel free to switch it to the
one-line declaration instead.

When adding a copyright line after completing a significant feature or rewrite,
add the newer line above the older one, like so:

.. code-block:: python

    #!/usr/bin/python
    
    # Copyright: (c) 2017, [New Contributor(s)]
    # Copyright: (c) 2015, [Original Contributor(s)]
    # GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

.. _ansible_metadata_block:

ANSIBLE_METADATA Block
----------------------

``ANSIBLE_METADATA`` contains information about the module for use by other tools. At the moment, it informs other tools which type of maintainer the module has and to what degree users can rely on a module's behaviour remaining the same over time.

For new modules, the following block can be simply added into your module

.. code-block:: python

   ANSIBLE_METADATA = {'metadata_version': '1.1',
                       'status': ['preview'],
                       'supported_by': 'community'}

.. warning::

   * ``metadata_version`` is the version of the ``ANSIBLE_METADATA`` schema, *not* the version of the module.
   * Promoting a module's ``status`` or ``supported_by`` status should only be done by members of the Ansible Core Team.

.. note:: Pre-released metadata version

    During development of Ansible-2.3, modules had an initial version of the
    metadata.  This version was modified slightly after release to fix some
    points of confusion.  You may occasionally see PRs for modules where the
    ANSIBLE_METADATA doesn't look quite right because of this.  Module
    metadata should be fixed before checking it into the repository.

Version 1.1 of the metadata
+++++++++++++++++++++++++++

Structure
^^^^^^^^^

.. code-block:: python

  ANSIBLE_METADATA = {
      'metadata_version': '1.1',
      'supported_by': 'community',
      'status': ['preview', 'deprecated']
  }

Fields
^^^^^^

:metadata_version: An "X.Y" formatted string. X and Y are integers which
   define the metadata format version. Modules shipped with Ansible are
   tied to an Ansible release, so we will only ship with a single version
   of the metadata. We'll increment Y if we add fields or legal values
   to an existing field. We'll increment X if we remove fields or values
   or change the type or meaning of a field.
   Current metadata_version is "1.1"
:supported_by: This field records who supports the module.
   Default value is ``community``. Values are:

   * core
   * network
   * certified
   * community
   * curated (Deprecated.  Modules in this category should probably be core or
     certified instead)

   For information on what the support level values entail, please see
   :ref:`Modules Support <modules_support>`.

:status: This field records information about the module that is
   important to the end user. It's a list of strings. The default value
   is a single element list ["preview"]. The following strings are valid
   statuses and have the following meanings:

   :stableinterface: This means that the module's parameters are
      stable. Every effort will be made not to remove parameters or change
      their meaning. It is not a rating of the module's code quality.
   :preview: This module is a tech preview. This means it may be
      unstable, the parameters may change, or it may require libraries or
      web services that are themselves subject to incompatible changes.
   :deprecated: This module is deprecated and will no longer be
      available in a future release.
   :removed: This module is not present in the release. A stub is
      kept so that documentation can be built. The documentation helps
      users port from the removed module to new modules.

Changes from Version 1.0
++++++++++++++++++++++++

:metadata_version: Version updated from 1.0 to 1.1
:supported_by: All substantive changes were to potential values of the supported_by field

  * Added the certified value
  * Deprecated the curated value, modules shipped with Ansible will use
    certified instead.  Third party modules are encouraged not to use this as
    it is meaningless within Ansible proper.
  * Added the network value

DOCUMENTATION Block
-------------------

See an example documentation string in the checkout under `examples/DOCUMENTATION.yml <https://github.com/ansible/ansible/blob/devel/examples/DOCUMENTATION.yml>`_.

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




The following fields can be used and are all required unless specified otherwise:

:module:
  The name of the module. This must be the same as the filename, without the ``.py`` extension.
:short_description:
  * A short description which is displayed on the :ref:`all_modules` page and ``ansible-doc -l``.
  * As the short description is displayed by ``ansible-doc -l`` without the category grouping it needs enough detail to explain its purpose without the context of the directory structure in which it lives.
  * Unlike ``description:`` this field should not have a trailing full stop.
:description:
  * A detailed description (generally two or more sentences).
  * Must be written in full sentences, i.e. with capital letters and fullstops.
  * Shouldn't mention the name module.
:version_added:
  The version of Ansible when the module was added.
  This is a `string`, and not a float, i.e. ``version_added: "2.1"``
:author:
  Name of the module author in the form ``First Last (@GitHubID)``. Use a multi-line list if there is more than one author.
:deprecated:
  If a module is deprecated it must be:

  * Mentioned in ``CHANGELOG``
  * Referenced in the ``porting_guide_x.y.rst``
  * File should be renamed to start with an ``_``
  * ``ANSIBLE_METADATA`` must contain ``status: ['deprecated']``
  * Following values must be set:

  :removed_in: A `string`, such as ``"2.9"``, which represents the version of Ansible this module will replaced with docs only module stub.
  :why: Optional string that used to detail why this has been removed.
  :alternative: Inform users they should do instead, i.e. ``Use M(whatmoduletouseinstead) instead.``.
:options:
  One per module argument:

  :option-name:

    * Declarative operation (not CRUD)–this makes it easy for a user not to care what the existing state is, just about the final state, for example `online:`, rather than `is_online:`.
    * The name of the option should be consistent with the rest of the module, as well as other modules in the same category.

  :description:

    * Detailed explanation of what this option does. It should be written in full sentences.
    * Should not list the options values (that's what ``choices:`` is for, though it should explain `what` the values do if they aren't obvious.
    * If an optional parameter is sometimes required this need to be reflected in the documentation, e.g. "Required when I(state=present)."
    * Mutually exclusive options must be documented as the final sentence on each of the options.
  :required:
    Only needed if true, otherwise it is assumed to be false.
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
  List of requirements, and minimum versions (if applicable)
:notes:
    Details of any important information that doesn't fit in one of the above sections; for example if ``check_mode`` isn't supported, or a link to external documentation.


.. note::

   - The above fields are are all in lowercase.

   - If the module doesn't doesn't have any options (for example, it's a ``_facts`` module), you can use ``options: {}``.

EXAMPLES block
--------------

The EXAMPLES section is required for all new modules.

Examples should demonstrate real world usage, and be written in multi-line plain-text YAML format.

Ensure that examples are kept in sync with the options during the PR review and any following code refactor.

As per playbook best practice, a `name:` should be specified.

``EXAMPLES`` string within the module like this::

    EXAMPLES = '''
    - name: Ensure foo is installed
      modulename:
        name: foo
        state: present
    '''

If the module returns facts that are often needed, an example of how to use them can be helpful.

RETURN Block
------------

The RETURN section documents what the module returns, and is required for all new modules.

For each value returned, provide a ``description``, in what circumstances the value is ``returned``,
the ``type`` of the value and a ``sample``.  For example, from the ``copy`` module:


The following fields can be used and are all required unless specified otherwise.

:return name:
  Name of the returned field.

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


For complex nested returns type can be specified as ``type: complex``.

Example::


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

.. note::

   If your module doesn't return anything (apart from the standard returns), you can use ``RETURN = ''' # '''``.


Python Imports
--------------

Starting with Ansible version 2.2, all new modules are required to use imports in the form:

.. code-block:: python

   from module_utils.basic import AnsibleModule


.. warning::

   The use of "wildcard" imports such as ``from module_utils.basic import *`` is no longer allowed.

Formatting functions
--------------------

The formatting functions are:

* ``L()`` for Links with a heading
* ``U()`` for URLs
* ``I()`` for option names
* ``C()`` for files and option values
* ``M()`` for module names.

Module names should be specified as ``M(module)`` to create a link to the online documentation for that module.


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
    See U(https://www.ansible.com/tower) for an overview.
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
