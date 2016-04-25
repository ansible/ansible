.. _flow_modules:

=======
Modules
=======

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
they're distinct entities for the purposes of this paper.  Action Plugins
always execute on the controller and are sometimes able to do all work there
(for instance, the debug Action Plugin which prints some text for the user to
see or the assert Action Plugin which can test whether several values in
a playbook satisfy certain criteria.)

More often, Action Plugins set up some values on the controller, then invoke an
actual module on the managed node that does something with these values.  An
easy to understand version of this is the :ref:`template Action Plugin
<template>`.  The :ref:`template Action Plugin <template>` takes values from
the user to construct a file in a temporary location on the controller using
variables from the playbook environment.  It then transfers the temporary file
to a temporary file on the remote system.  After that, it invokes the
:ref:`copy module <copy>` which operates on the remote system to move the file
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

New-style Python modules use the :ref:`ziploader` framework for constructing
modules.  All official modules (shipped with Ansible) use either this or the
:ref:`powershell module framework <flow_powershell_modules>`.

These modules use imports from :code:`ansible.module_utils` in order to pull in
boilerplate module code, such as argument parsing, formatting of return
values as :term:`JSON`, and various file operations.

.. note:: In Ansible, up to version 2.0.x, the official Python modules used the
    :ref:`module_replacer` framework.  For module authors, :ref:`ziploader` is
    largely a superset of :ref:`module_replacer` functionality, so you usually
    do not need to know about one versus the other.

.. _flow_powershell_modules:

Powershell
^^^^^^^^^^

New-style powershell modules use the :ref:`module_replacer` framework for
constructing modules.  These modules get a library of powershell code embedded
in them before being sent to the managed node.

.. _flow_josnargs_modules:

JSONARGS
^^^^^^^^

Scripts can arrange for an argument string to be placed within them by placing
the string ``<<INCLUDE_ANSIBLE_MODULE_JSON_ARGS>>`` somewhere inside of the
file.  The module typically sets a variable to that value like this::

    json_arguments = """<<INCLUDE_ANSIBLE_MODULE_JSON_ARGS>>"""

Which is expanded as::

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
  instantiating a Connection class according to the inventory configuration for
  that host.
* It adds any internal Ansible variables to the module's parameters (for
  instance, the ones that pass along ``no_log`` to the module).
* It takes care of creating any temporary files on the remote machine and
  cleans up afterwards.
* It does the actual work of pushing the module and module parameters to the
  remote host, although the :ref:`module_common <flow_executor_module_common>`
  code described next does the work of deciding which format those will take.
* It handles any special cases regarding modules (for instance, various
  complications around Windows modules that must have the same names as Python
  modules, so that internal calling of modules from other Action Plugins work.)

Much of this functionality comes from the :class:`BaseAction` class,
which lives in :file:`plugins/action/__init__.py`.  It makes use of Connection
and Shell objects to do its work.

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
:ref:`Python modules <flow_python_modules>` are assembled by :ref:`ziploader`.
:ref:`Non-native-want-JSON <flow_want_json_modules>` and
:ref:`Old-Style modules <flow_old_style_modules>` aren't touched by either of
these and pass through unchanged.  After the assembling step, one final
modification is made to all modules that have a shebang line.  Ansible checks
whether the interpreter in the shebang line has a specific path configured via
an ``ansible_$X_interpreter`` inventory variable.  If it does, Ansible
substitutes that path for the interpreter path given in the module.  After
this Ansible returns the complete module data and the module type to the
:ref:`Normal Action <_flow_normal_action_plugin>` which continues execution of
the module.

Next we'll go into some details of the two assembler frameworks.

.. _module_replacer:

Module Replacer
^^^^^^^^^^^^^^^

The Module Replacer is essentially a preprocessor (like the C Preprocessor for
those familiar with that language).  It does straight substitutions of
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
    a new-style Python module, it's better to use ``from ansible import
    __version__`` and then use ``__version__`` instead.
  - :code:`"<<INCLUDE_ANSIBLE_MODULE_COMPLEX_ARGS>>"` is substituted with
    a string which is the Python ``repr`` of the :term:`JSON` encoded module
    parameters.  Using ``repr`` on the JSON string makes it safe to embed in
    a Python file.  In :ref:`new-style Python modules <flow_python_modules>`
    under :ref:`ziploader` this is passed in via an environment variable
    instead.
  - :code:`<<SELINUX_SPECIAL_FILESYSTEMS>>` substitutes a string which is
    a comma separated list of file systems which have a file system dependent
    security context in SELinux.  In new-style Python modules, this is found
    by looking up ``SELINUX_SPECIAL_FS`` from the
    :envvar:`ANSIBLE_MODULE_CONSTANTS` environment variable.  See the
    :ref:`ziploader` documentation for details.
  - :code:`<<INCLUDE_ANSIBLE_MODULE_JSON_ARGS>>` substitutes the module
    parameters as a JSON string.  Care must be taken to properly quote the
    string as JSON data may contain quotes.  This pattern is not substituted
    in new-style Python modules as they can get the module parameters via the
    environment variable.
  - the string :code:`syslog.LOG_USER` is replaced wherever it occurs with the
    value of ``syslog_facility`` from the :file:`ansible.cfg` or any
    ``ansible_syslog_facility`` inventory variable that applies to this host.  In
    new-style Python modules, you can get the value of the ``syslog_facility``
    by looking up ``SYSLOG_FACILITY`` in the :envvar:`ANSIBLE_MODULE_CONSTANTS`
    environment variable.  See the :ref:`ziploader` documentation for details.

.. _ziploader:

ziploader
^^^^^^^^^

Ziploader differs from :ref:`module_replacer` in that it uses real Python
imports of things in module_utils instead of merely preprocessing the module.
It does this by constructing a zipfile--which includes the module file, files
in :file:`ansible/module_utils` that are imported by the module, and some
boilerplate to pass in the constants.  The zipfile is then Base64 encoded and
wrapped in a small Python script which decodes the Base64 encoding and places
the zipfile into a temp direcrtory on the managed node.  It then extracts just
the ansible module script from the zip file and places that in the temporary
directory as well.  Then it sets the PYTHONPATH to find python modules inside
of the zip file and invokes :command:`python` on the extracted ansible module.

.. note::
    Ansible wraps the zipfile in the Python script for two reasons:

    * for compatibility with Python-2.4 and Python-2.6 which have less
      featureful versions of Python's ``-m`` command line switch.
    * so that pipelining will function properly.  Pipelining needs to pipe the
      Python module into the Python interpreter on the remote node.  Python
      understands scripts on stdin but does not understand zip files.

In ziploader, any imports of Python modules from the ``ansible.module_utils``
package trigger inclusion of that Python file into the zipfile.  Instances of
:code:`#<<INCLUDE_ANSIBLE_MODULE_COMMON>>` in the module are turned into
:code:`from ansible.module_utils.basic import *` and
:file:`ansible/module-utils/basic.py` is then included in the zipfile.  Files
that are included from module_utils are themselves scanned for imports of other
Python modules from module_utils to be included in the zipfile as well.

.. warning::
    At present, Ziploader cannot determine whether an import should be
    included if it is a relative import.  Always use an absolute import that
    has ``ansible.module_utils`` in it to allow ziploader to determine that
    the file should be included.

.. _flow_passing_module_args:

Passing args
~~~~~~~~~~~~

In :ref:`module_replacer`, module arguments are turned into a JSON-ified
string and substituted into the combined module file.  In :ref:`ziploader`,
the JSON-ified string is passed into the module via stdin.  When
a  :class:`ansible.module_utils.basic.AnsibleModule` is instantiated,
it parses this string and places the args into
:attribute:`AnsibleModule.params` where it can be accessed by the module's
other code.

.. _flow_passing_module_constants:

Passing constants
~~~~~~~~~~~~~~~~~

Currently, there are three constants passed from the controller to the modules:
``ANSIBLE_VERSION``, ``SELINUX_SPECIAL_FS``, and ``SYSLOG_FACILITY``.  In
:ref:`module_replacer`, ``ANSIBLE_VERSION`` and ``SELINUX_SPECIAL_FS`` were
substituted into the global variables
:code:`ansible.module_utils.basic.ANSIBLE_VERSION` and
:code:`ansible.module_utils.basic.SELINUX_SPECIAL_FS`.  ``SYSLOG_FACILITY`` didn't
get placed into a variable.  Instead, any occurrences of the string
``syslog.LOG_USER`` in the combined module file were replaced with ``syslog.``
followed by the string contained in ``SYSLOG_FACILITY``.  All of these have
changed in :ref:`ziploader`.

The Ansible verison can now be used by a module by importing ``__version__``
from ansible::

    from ansible import __version__
    module.exit_json({'msg': 'module invoked by ansible %s' % __version__})

For now, :code:`ANSIBLE_VERSION` is also available at its old location inside of
``ansible.module_utils.basic``, but that will eventually be removed.

``SELINUX_SPECIAL_FS`` and  ``SYSLOG_FACILITY`` have changed much more.
:ref:`ziploader` passes these as part of the JSON-ified argument string via stdin.
When
:class:`ansible.module_utils.basic.AnsibleModule` is instantiated, it parses this
string and places the constants into :attribute:`AnsibleModule.constants`
where other code can access it.

Unlike the ``ANSIBLE_VERSION``, where some efforts were made to keep the old
backwards compatible globals available, these two constants are not available
at their old names.  This is a combination of the degree to which these are
internal to the needs of ``module_utils.basic`` and, in the case of
``SYSLOG_FACILITY``, how hacky and unsafe the previous implementation was.

Porting code from the :ref:`module_replacer` method of getting
``SYSLOG_FACILITY`` to the new one is a little more tricky than the other
constants and args, due to just how hacky the old way was.  Here's an example
of using it in the new way::

        import syslog
        facility_name = module.constants.get('SYSLOG_FACILITY')
        facility = getattr(syslog, facility_name)
        syslog.openlog(str(module), 0, facility)

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
