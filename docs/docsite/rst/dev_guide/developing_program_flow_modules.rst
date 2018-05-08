.. _flow_modules:

===========================
Ansible Module Architecture
===========================

This in-depth dive helps you understand Ansible's program flow to execute
modules. It is written for people working on the portions of the Core Ansible
Engine that execute a module. Those writing Ansible Modules may also find this
in-depth dive to be of interest, but individuals simply using Ansible Modules
will not likely find this to be helpful.

.. _flow_types_of_modules:

Types of Modules
================

Ansible supports several different types of modules in its code base.  Some of
these are for backwards compatibility and others are to enable flexibility.

.. _flow_action_plugins:

Action Plugins
--------------

Action Plugins look like modules to end users who are writing :term:`playbooks` but
they're distinct entities for the purposes of this document.  Action Plugins
always execute on the controller and are sometimes able to do all work there
(for instance, the ``debug`` Action Plugin which prints some text for the user to
see or the ``assert`` Action Plugin which can test whether several values in
a playbook satisfy certain criteria.)

More often, Action Plugins set up some values on the controller, then invoke an
actual module on the managed node that does something with these values.  An
easy to understand version of this is the :ref:`template Action Plugin
<template_module>`.  The :ref:`template Action Plugin <template_module>` takes values from
the user to construct a file in a temporary location on the controller using
variables from the playbook environment.  It then transfers the temporary file
to a temporary file on the remote system.  After that, it invokes the
:ref:`copy module <copy_module>` which operates on the remote system to move the file
into its final location, sets file permissions, and so on.

.. _flow_new_style_modules:

New-style Modules
-----------------

All of the modules that ship with Ansible fall into this category.

New-style modules have the arguments to the module embedded inside of them in
some manner.  Non-new-style modules must copy a separate file over to the
managed node, which is less efficient as it requires two over-the-wire
connections instead of only one.

.. _flow_python_modules:

Python
^^^^^^

New-style Python modules use the :ref:`Ansiballz` framework for constructing
modules.  All official modules (shipped with Ansible) use either this or the
:ref:`powershell module framework <flow_powershell_modules>`.

These modules use imports from :code:`ansible.module_utils` in order to pull in
boilerplate module code, such as argument parsing, formatting of return
values as :term:`JSON`, and various file operations.

.. note:: In Ansible, up to version 2.0.x, the official Python modules used the
    :ref:`module_replacer` framework.  For module authors, :ref:`Ansiballz` is
    largely a superset of :ref:`module_replacer` functionality, so you usually
    do not need to know about one versus the other.

.. _flow_powershell_modules:

Powershell
^^^^^^^^^^

New-style powershell modules use the :ref:`module_replacer` framework for
constructing modules.  These modules get a library of powershell code embedded
in them before being sent to the managed node.

.. _flow_jsonargs_modules:

JSONARGS
^^^^^^^^

Scripts can arrange for an argument string to be placed within them by placing
the string ``<<INCLUDE_ANSIBLE_MODULE_JSON_ARGS>>`` somewhere inside of the
file.  The module typically sets a variable to that value like this:

.. code-block:: python

    json_arguments = """<<INCLUDE_ANSIBLE_MODULE_JSON_ARGS>>"""

Which is expanded as:

.. code-block:: python

    json_arguments = """{"param1": "test's quotes", "param2": "\"To be or not to be\" - Hamlet"}"""

.. note:: Ansible outputs a :term:`JSON` string with bare quotes.  Double quotes are
       used to quote string values, double quotes inside of string values are
       backslash escaped, and single quotes may appear unescaped inside of
       a string value.  To use JSONARGS, your scripting language must have a way
       to handle this type of string.  The example uses Python's triple quoted
       strings to do this.  Other scripting languages may have a similar quote
       character that won't be confused by any quotes in the JSON or it may
       allow you to define your own start-of-quote and end-of-quote characters.
       If the language doesn't give you any of these then you'll need to write
       a :ref:`non-native JSON module <flow_want_json_modules>` or
       :ref:`Old-style module <flow_old_style_modules>` instead.

The module typically parses the contents of ``json_arguments`` using a JSON
library and then use them as native variables throughout the rest of its code.

.. _flow_want_json_modules:

Non-native want JSON modules
----------------------------

If a module has the string ``WANT_JSON`` in it anywhere, Ansible treats
it as a non-native module that accepts a filename as its only command line
parameter.  The filename is for a temporary file containing a :term:`JSON`
string containing the module's parameters.  The module needs to open the file,
read and parse the parameters, operate on the data, and print its return data
as a JSON encoded dictionary to stdout before exiting.

These types of modules are self-contained entities.  As of Ansible 2.1, Ansible
only modifies them to change a shebang line if present.

.. seealso:: Examples of Non-native modules written in ruby are in the `Ansible
    for Rubyists <https://github.com/ansible/ansible-for-rubyists>`_ repository.

.. _flow_binary_modules:

Binary Modules
--------------

From Ansible 2.2 onwards, modules may also be small binary programs.  Ansible
doesn't perform any magic to make these portable to different systems so they
may be specific to the system on which they were compiled or require other
binary runtime dependencies.  Despite these drawbacks, a site may sometimes
have no choice but to compile a custom module against a specific binary
library if that's the only way they have to get access to certain resources.

Binary modules take their arguments and will return data to Ansible in the same
way as :ref:`want JSON modules <flow_want_json_modules>`.

.. seealso:: One example of a `binary module
    <https://github.com/ansible/ansible/blob/devel/test/integration/targets/binary_modules/library/helloworld.go>`_
    written in go.

.. _flow_old_style_modules:

Old-style Modules
-----------------

Old-style modules are similar to
:ref:`want JSON modules <flow_want_json_modules>`, except that the file that
they take contains ``key=value`` pairs for their parameters instead of
:term:`JSON`.

Ansible decides that a module is old-style when it doesn't have any of the
markers that would show that it is one of the other types.

.. _flow_how_modules_are_executed:

How modules are executed
========================

When a user uses :program:`ansible` or :program:`ansible-playbook`, they
specify a task to execute.  The task is usually the name of a module along
with several parameters to be passed to the module.  Ansible takes these
values and processes them in various ways before they are finally executed on
the remote machine.

.. _flow_executor_task_executor:

executor/task_executor
----------------------

The TaskExecutor receives the module name and parameters that were parsed from
the :term:`playbook <playbooks>` (or from the command line in the case of
:command:`/usr/bin/ansible`).  It uses the name to decide whether it's looking
at a module or an :ref:`Action Plugin <flow_action_plugins>`.  If it's
a module, it loads the :ref:`Normal Action Plugin <flow_normal_action_plugin>`
and passes the name, variables, and other information about the task and play
to that Action Plugin for further processing.

.. _flow_normal_action_plugin:

Normal Action Plugin
--------------------

The ``normal`` Action Plugin executes the module on the remote host.  It is
the primary coordinator of much of the work to actually execute the module on
the managed machine.

* It takes care of creating a connection to the managed machine by
  instantiating a ``Connection`` class according to the inventory
  configuration for that host.
* It adds any internal Ansible variables to the module's parameters (for
  instance, the ones that pass along ``no_log`` to the module).
* It takes care of creating any temporary files on the remote machine and
  cleans up afterwards.
* It does the actual work of pushing the module and module parameters to the
  remote host, although the :ref:`module_common <flow_executor_module_common>`
  code described in the next section does the work of deciding which format
  those will take.
* It handles any special cases regarding modules (for instance, various
  complications around Windows modules that must have the same names as Python
  modules, so that internal calling of modules from other Action Plugins work.)

Much of this functionality comes from the `BaseAction` class,
which lives in :file:`plugins/action/__init__.py`.  It makes use of
``Connection`` and ``Shell`` objects to do its work.

.. note::
    When :term:`tasks <tasks>` are run with the ``async:`` parameter, Ansible
    uses the ``async`` Action Plugin instead of the ``normal`` Action Plugin
    to invoke it.  That program flow is currently not documented.  Read the
    source for information on how that works.

.. _flow_executor_module_common:

executor/module_common.py
-------------------------

Code in :file:`executor/module_common.py` takes care of assembling the module
to be shipped to the managed node.  The module is first read in, then examined
to determine its type.  :ref:`PowerShell <flow_powershell_modules>` and
:ref:`JSON-args modules <flow_jsonargs_modules>` are passed through
:ref:`Module Replacer <module_replacer>`.  New-style
:ref:`Python modules <flow_python_modules>` are assembled by :ref:`Ansiballz`.
:ref:`Non-native-want-JSON <flow_want_json_modules>`,
:ref:`Binary modules <flow_binary_modules>`, and
:ref:`Old-Style modules <flow_old_style_modules>` aren't touched by either of
these and pass through unchanged.  After the assembling step, one final
modification is made to all modules that have a shebang line.  Ansible checks
whether the interpreter in the shebang line has a specific path configured via
an ``ansible_$X_interpreter`` inventory variable.  If it does, Ansible
substitutes that path for the interpreter path given in the module.  After
this, Ansible returns the complete module data and the module type to the
:ref:`Normal Action <flow_normal_action_plugin>` which continues execution of
the module.

Next we'll go into some details of the two assembler frameworks.

.. _module_replacer:

Module Replacer
^^^^^^^^^^^^^^^

The Module Replacer framework is the original framework implementing new-style
modules.  It is essentially a preprocessor (like the C Preprocessor for those
familiar with that programming language).  It does straight substitutions of
specific substring patterns in the module file.  There are two types of
substitutions:

* Replacements that only happen in the module file.  These are public
  replacement strings that modules can utilize to get helpful boilerplate or
  access to arguments.

  - :code:`from ansible.module_utils.MOD_LIB_NAME import *` is replaced with the
    contents of the :file:`ansible/module_utils/MOD_LIB_NAME.py`  These should
    only be used with :ref:`new-style Python modules <flow_python_modules>`.
  - :code:`#<<INCLUDE_ANSIBLE_MODULE_COMMON>>` is equivalent to
    :code:`from ansible.module_utils.basic import *` and should also only apply
    to new-style Python modules.
  - :code:`# POWERSHELL_COMMON` substitutes the contents of
    :file:`ansible/module_utils/powershell.ps1`.  It should only be used with
    :ref:`new-style Powershell modules <flow_powershell_modules>`.

* Replacements that are used by ``ansible.module_utils`` code.  These are internal
  replacement patterns.  They may be used internally, in the above public
  replacements, but shouldn't be used directly by modules.

  - :code:`"<<ANSIBLE_VERSION>>"` is substituted with the Ansible version.  In
    :ref:`new-style Python modules <flow_python_modules>` under the
    :ref:`Ansiballz` framework the proper way is to instead instantiate an
    `AnsibleModule` and then access the version from
    :attr:``AnsibleModule.ansible_version``.
  - :code:`"<<INCLUDE_ANSIBLE_MODULE_COMPLEX_ARGS>>"` is substituted with
    a string which is the Python ``repr`` of the :term:`JSON` encoded module
    parameters.  Using ``repr`` on the JSON string makes it safe to embed in
    a Python file.  In new-style Python modules under the Ansiballz framework
    this is better accessed by instantiating an `AnsibleModule` and
    then using :attr:`AnsibleModule.params`.
  - :code:`<<SELINUX_SPECIAL_FILESYSTEMS>>` substitutes a string which is
    a comma separated list of file systems which have a file system dependent
    security context in SELinux.  In new-style Python modules, if you really
    need this you should instantiate an `AnsibleModule` and then use
    :attr:`AnsibleModule._selinux_special_fs`.  The variable has also changed
    from a comma separated string of file system names to an actual python
    list of filesystem names.
  - :code:`<<INCLUDE_ANSIBLE_MODULE_JSON_ARGS>>` substitutes the module
    parameters as a JSON string.  Care must be taken to properly quote the
    string as JSON data may contain quotes.  This pattern is not substituted
    in new-style Python modules as they can get the module parameters another
    way.
  - The string :code:`syslog.LOG_USER` is replaced wherever it occurs with the
    ``syslog_facility`` which was named in :file:`ansible.cfg` or any
    ``ansible_syslog_facility`` inventory variable that applies to this host.  In
    new-style Python modules this has changed slightly.  If you really need to
    access it, you should instantiate an `AnsibleModule` and then use
    :attr:`AnsibleModule._syslog_facility` to access it.  It is no longer the
    actual syslog facility and is now the name of the syslog facility.  See
    the :ref:`documentation on internal arguments <flow_internal_arguments>`
    for details.

.. _Ansiballz:

Ansiballz
^^^^^^^^^

Ansible 2.1 switched from the :ref:`module_replacer` framework to the
Ansiballz framework for assembling modules.  The Ansiballz framework differs
from module replacer in that it uses real Python imports of things in
:file:`ansible/module_utils` instead of merely preprocessing the module.  It
does this by constructing a zipfile -- which includes the module file, files
in :file:`ansible/module_utils` that are imported by the module, and some
boilerplate to pass in the module's parameters.  The zipfile is then Base64
encoded and wrapped in a small Python script which decodes the Base64 encoding
and places the zipfile into a temp directory on the managed node.  It then
extracts just the ansible module script from the zip file and places that in
the temporary directory as well.  Then it sets the PYTHONPATH to find python
modules inside of the zip file and invokes :command:`python` on the extracted
ansible module.

.. note::
    Ansible wraps the zipfile in the Python script for two reasons:

    * for compatibility with Python-2.6 which has a less
      functional version of Python's ``-m`` command line switch.
    * so that pipelining will function properly.  Pipelining needs to pipe the
      Python module into the Python interpreter on the remote node.  Python
      understands scripts on stdin but does not understand zip files.

In Ansiballz, any imports of Python modules from the
:py:mod:`ansible.module_utils` package trigger inclusion of that Python file
into the zipfile.  Instances of :code:`#<<INCLUDE_ANSIBLE_MODULE_COMMON>>` in
the module are turned into :code:`from ansible.module_utils.basic import *`
and :file:`ansible/module-utils/basic.py` is then included in the zipfile.
Files that are included from :file:`module_utils` are themselves scanned for
imports of other Python modules from :file:`module_utils` to be included in
the zipfile as well.

.. warning::
    At present, the Ansiballz Framework cannot determine whether an import
    should be included if it is a relative import.  Always use an absolute
    import that has :py:mod:`ansible.module_utils` in it to allow Ansiballz to
    determine that the file should be included.

.. _flow_passing_module_args:

Passing args
~~~~~~~~~~~~

In :ref:`module_replacer`, module arguments are turned into a JSON-ified
string and substituted into the combined module file.  In :ref:`Ansiballz`,
the JSON-ified string is passed into the module via stdin.  When
a  :class:`ansible.module_utils.basic.AnsibleModule` is instantiated,
it parses this string and places the args into
:attr:`AnsibleModule.params` where it can be accessed by the module's
other code.

.. note::
    Internally, the `AnsibleModule` uses the helper function,
    :py:func:`ansible.module_utils.basic._load_params`, to load the parameters
    from stdin and save them into an internal global variable.  Very dynamic
    custom modules which need to parse the parameters prior to instantiating
    an ``AnsibleModule`` may use ``_load_params`` to retrieve the
    parameters.  Be aware that ``_load_params`` is an internal function and
    may change in breaking ways if necessary to support changes in the code.
    However, we'll do our best not to break it gratuitously, which is not
    something that can be said for either the way parameters are passed or
    the internal global variable.

.. _flow_internal_arguments:

Internal arguments
^^^^^^^^^^^^^^^^^^

Both :ref:`module_replacer` and :ref:`Ansiballz` send additional arguments to
the module beyond those which the user specified in the playbook.  These
additional arguments are internal parameters that help implement global
Ansible features.  Modules often do not need to know about these explicitly as
the features are implemented in :py:mod:`ansible.module_utils.basic` but certain
features need support from the module so it's good to know about them.

_ansible_no_log
~~~~~~~~~~~~~~~

This is a boolean.  If it's True then the playbook specified ``no_log`` (in
a task's parameters or as a play parameter).  This automatically affects calls
to :py:meth:`AnsibleModule.log`.  If a module implements its own logging then
it needs to check this value.  The best way to look at this is for the module
to instantiate an `AnsibleModule` and then check the value of
:attr:`AnsibleModule.no_log`.

.. note::
    ``no_log`` specified in a module's argument_spec are handled by a different mechanism.

_ansible_debug
~~~~~~~~~~~~~~

This is a boolean that turns on more verbose logging.  If a module uses
:py:meth:`AnsibleModule.debug` rather than :py:meth:`AnsibleModule.log` then
the messages are only logged if this is True.  This also turns on logging of
external commands that the module executes.  This can be changed via
the ``debug`` setting in :file:`ansible.cfg` or the environment variable
:envvar:`ANSIBLE_DEBUG`.  If, for some reason, a module must access this, it
should do so by instantiating an `AnsibleModule` and accessing
:attr:`AnsibleModule._debug`.

_ansible_diff
~~~~~~~~~~~~~

This boolean is turned on via the ``--diff`` command line option.  If a module
supports it, it will tell the module to show a unified diff of changes to be
made to templated files.  The proper way for a module to access this is by
instantiating an `AnsibleModule` and accessing
:attr:`AnsibleModule._diff`.

_ansible_verbosity
~~~~~~~~~~~~~~~~~~

This value could be used for finer grained control over logging. However, it
is currently unused.

_ansible_selinux_special_fs
~~~~~~~~~~~~~~~~~~~~~~~~~~~

This is a list of names of filesystems which should have a special selinux
context.  They are used by the `AnsibleModule` methods which operate on
files (changing attributes, moving, and copying).  The list of names is set
via a comma separated string of filesystem names from :file:`ansible.cfg`::

  # ansible.cfg
  [selinux]
  special_context_filesystems=nfs,vboxsf,fuse,ramfs

If a module cannot use the builtin ``AnsibleModule`` methods to manipulate
files and needs to know about these special context filesystems, it should
instantiate an ``AnsibleModule`` and then examine the list in
:attr:`AnsibleModule._selinux_special_fs`.

This replaces :attr:`ansible.module_utils.basic.SELINUX_SPECIAL_FS` from
:ref:`module_replacer`.  In module replacer it was a comma separated string of
filesystem names.  Under Ansiballz it's an actual list.

.. versionadded:: 2.1

_ansible_syslog_facility
~~~~~~~~~~~~~~~~~~~~~~~~

This parameter controls which syslog facility ansible module logs to.  It may
be set by changing the ``syslog_facility`` value in :file:`ansible.cfg`.  Most
modules should just use :meth:`AnsibleModule.log` which will then make use of
this.  If a module has to use this on its own, it should instantiate an
`AnsibleModule` and then retrieve the name of the syslog facility from
:attr:`AnsibleModule._syslog_facility`.  The code will look slightly different
than it did under :ref:`module_replacer` due to how hacky the old way was

.. code-block:: python

        # Old way
        import syslog
        syslog.openlog(NAME, 0, syslog.LOG_USER)

        # New way
        import syslog
        facility_name = module._syslog_facility
        facility = getattr(syslog, facility_name, syslog.LOG_USER)
        syslog.openlog(NAME, 0, facility)

.. versionadded:: 2.1

_ansible_version
~~~~~~~~~~~~~~~~

This parameter passes the version of ansible that runs the module.  To access
it, a module should instantiate an `AnsibleModule` and then retrieve it
from :attr:`AnsibleModule.ansible_version`.  This replaces
:attr:`ansible.module_utils.basic.ANSIBLE_VERSION` from
:ref:`module_replacer`.

.. versionadded:: 2.1

.. _flow_special_considerations:

Special Considerations
----------------------

.. _flow_pipelining:

Pipelining
^^^^^^^^^^

Ansible can transfer a module to a remote machine in one of two ways:

* it can write out the module to a temporary file on the remote host and then
  use a second connection to the remote host to execute it with the
  interpreter that the module needs
* or it can use what's known as pipelining to execute the module by piping it
  into the remote interpreter's stdin.

Pipelining only works with modules written in Python at this time because
Ansible only knows that Python supports this mode of operation.  Supporting
pipelining means that whatever format the module payload takes before being
sent over the wire must be executable by Python via stdin.

.. _flow_args_over_stdin:

Why pass args over stdin?
^^^^^^^^^^^^^^^^^^^^^^^^^

Passing arguments via stdin was chosen for the following reasons:

* When combined with :ref:`ANSIBLE_PIPELINING`, this keeps the module's arguments from
  temporarily being saved onto disk on the remote machine.  This makes it
  harder (but not impossible) for a malicious user on the remote machine to
  steal any sensitive information that may be present in the arguments.
* Command line arguments would be insecure as most systems allow unprivileged
  users to read the full commandline of a process.
* Environment variables are usually more secure than the commandline but some
  systems limit the total size of the environment.  This could lead to
  truncation of the parameters if we hit that limit.


.. _ansiblemodule:

AnsibleModule
-------------

.. _argument_spec:

Argument Spec
^^^^^^^^^^^^^

The ``argument_spec`` provided to ``AnsibleModule`` defines the supported arguments for a module, as well as their type, defaults and more.

Example ``argument_spec``:

.. code-block:: python

    module = AnsibleModule(argument_spec=dict(
        top_level=dict(
            type='dict',
            options=dict(
                second_level=dict(
                    default=True,
                    type='bool',
                )
            )
        )
    ))

This section will discss the behavioral attributes for arguments

type
~~~~

``type`` allows you to define the type of the value accepted for the argument. The default value for ``type`` is ``str``. Possible values are:

* str
* list
* dict
* bool
* int
* float
* path
* raw
* jsonarg
* json
* bytes
* bits

The ``raw`` type, performs no type validation or type casing, and maintains the type of the passed value.

elements
~~~~~~~~

``elements`` works in combination with ``type`` when ``type='list'``. ``elements`` can then be defined as ``elements='int'`` or any other type, indicating that each element of the specified list should be of that type.

default
~~~~~~~

The ``default`` option allows sets a default value for the argument for the scenario when the argument is not provided to the module. When not specified, the default value is ``None``.

fallback
~~~~~~~~

``fallback`` accepts a ``tuple`` where the first argument is a callable (function) that will be used to perform the lookup, based on the second argument. The second argument is a list of values to be accepted by the callable.

The most common callable used is ``env_fallback`` which will allow an argument to optionally use an environment variable when the argument is not supplied.

Example::

    username=dict(fallback=(env_fallback, ['ANSIBLE_NET_USERNAME']))

choices
~~~~~~~

``choices`` accepts a list of choices that the argument will accept. The types of ``choices`` should match the ``type``.

required
~~~~~~~~

``required`` accepts a boolean, either ``True`` or ``False`` that indicates that the argument is required. This should not be used in combination with ``default``.

no_log
~~~~~~

``no_log`` indicates that the value of the argument should not be logged or displayed.

aliases
~~~~~~~

``aliases`` accepts a list of alternative argument names for the argument, such as the case where the argument is ``name`` but the module accepts ``aliases=['pkg']`` to allow ``pkg`` to be interchangably with ``name``

options
~~~~~~~

``options`` implements the ability to create a sub-argument_spec, where the sub options of the top level argument are also validated using the attributes discussed in this section. The example at the top of this section demonstrates use of ``options``. ``type`` or ``elements`` should be ``dict`` is this case.

apply_defaults
~~~~~~~~~~~~~~

``apply_defaults`` works alongside ``options`` and allows the ``default`` of the sub-options to be applied even when the top-level argument is not supplied.

In the example of the ``argument_spec`` at the top of this section, it would allow ``module.params['top_level']['second_level']`` to be defined, even if the user does not provide ``top_level`` when calling the module.

removed_in_version
~~~~~~~~~~~~~~~~~~

``removed_in_version`` indicates which version of Ansible a deprecated argument will be removed in.
