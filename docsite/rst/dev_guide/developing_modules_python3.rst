===========================
Porting Modules to Python 3
===========================

Ansible modules are not the usual Python-3 porting exercise.  There are two
factors that make it harder to port them than most code:

1. Many modules need to run on Python-2.4 in addition to Python-3.
2. A lot of mocking has to go into unittesting a Python-3 module.  So it's
   harder to test that your porting has fixed everything or to make sure that
   later commits haven't regressed.

Which version of Python-3.x and which version of Python-2.x are our minimums?
=============================================================================

The short answer is Python-3.4 and Python-2.4 but please read on for more
information.

For Python-3 we are currently using Python-3.4 as a minimum.  However, no long
term supported Linux distributions currently ship with Python-3.  When that
occurs, we will probably take that as our minimum Python-3 version rather than
Python-3.4.  Thus far, Python-3 has been adding small changes that make it
more compatible with Python-2 in its newer versions (For instance, Python-3.5
added the ability to use percent-formatted byte strings.) so it should be more
pleasant to use a newer version of Python-3 if it's available.  At some point
this will change but we'll just have to cross that bridge when we get to it.

For Python-2 the default is for modules to run on Python-2.4.  This allows
users with older distributions that are stuck on Python-2.4 to manage their
machines.  Modules are allowed to drop support for Python-2.4 when one of
their dependent libraries require a higher version of python.  This is not an
invitation to add unnecessary dependent libraries in order to force your
module to be usable only with a newer version of Python.  Instead it is an
acknowledgment that some libraries (for instance, boto3 and docker-py) will
only function with newer Python.

.. note:: When will we drop support for Python-2.4?

    The only long term supported distro that we know of with Python-2.4 is
    RHEL5 (and its rebuilds like CentOS5)  which is supported until April of
    2017.  We will likely end our support for Python-2.4 in modules in an
    Ansible release around that time.  We know of no long term supported
    distributions with Python-2.5 so the new minimum Python-2 version will
    likely be Python-2.6.  This will let us take advantage of the
    forwards-compat features of Python-2.6 so porting and maintainance of
    Python-2/Python-3 code will be easier after that.

Supporting only Python-2 or only Python-3
=========================================

Sometimes a module's dependent libraries only run on Python-2 or only run on
Python-3.  We do not yet have a strategy for these modules but we'll need to
come up with one.  I see three possibilities:

1. We treat these libraries like any other libraries that may not be installed
   on the system.  When we import them we check if the import was successful.
   If so, then we continue.  If not we return an error about the library being
   missing.  Users will have to find out that the library is unavailable on
   their version of Python either by searching for the library on their own or
   reading the requirements section in :command:`ansible-doc`.

2. The shebang line is the only metadata that Ansible extracts from a module
   so we may end up using that to specify what we mean.  Something like
   ``#!/usr/bin/python`` means the module will run on both Python-2 and
   Python-3, ``#!/usr/bin/python2`` means the module will only run on
   Python-2, and ``#!/usr/bin/python3`` means the module will only run on
   Python-3.  Ansible's code will need to be modified to accommodate this.
   For :command:`python2`, if ``ansible_python2_interpreter`` is not set, it
   will have to fallback to `` ansible_python_interpreter`` and if that's not
   set, fallback to ``/usr/bin/python``.  For :command:`python3`,  Ansible
   will have to first try ``ansible_python3_interpreter`` and then fallback to
   ``/usr/bin/python3`` as normal.

3. We add a way for Ansible to retrieve metadata about modules.  The metadata
   will include the version of Python that is required.

Methods 2 and 3 will both require that we modify modules or otherwise add this
additional information somewhere.  2 needs only a little code changes in
executor/module_common.py to parse.  3 will require a lot of work.  This is
probably not worthwhile if this is the only change but could be worthwhile if
there's other things as well.  1 requires that we port all modules to work
with python3 syntax but only the code path to get to the library import being
attempted and then a fail_json() being called because the libraries are
unavailable needs to actually work.

Tips, tricks, and idioms to adopt
=================================

Exceptions
----------

In code which already needs Python-2.6+ (For instance, because a library it
depends on only runs on Python >= 2.6) it is okay to port directly to the new
exception catching syntax::

    try:
        a = 2/0
    except ValueError as e:
        module.fail_json(msg="Tried to divide by zero!")

For modules which also run on Python-2.4, we have to use an uglier
construction to make this work under both Python-2.4 and Python-3::

    from ansible.module_utils.pycompat24 import get_exception
    [...]

    try:
        a = 2/0
    except ValueError:
        e = get_exception()
        module.fail_json(msg="Tried to divide by zero!")

Octal numbers
-------------

In Python-2.4, octal literals are specified as ``0755``.  In Python-3, that is
invalid and octals must be specified as ``0o755``.  To bridge this gap,
modules should create their octals like this::

    # Can't use 0755 on Python-3 and can't use 0o755 on Python-2.4
    EXECUTABLE_PERMS = int('0755', 8)

Bundled six
-----------

The third-party python-six library exists to help projects create code that
runs on both Python-2 and Python-3.  Ansible includes version 1.4.1 in
module_utils so that other modules can use it without requiring that it is
installed on the remote system.  To make use of it, import it like this::

    from ansible.module_utils import six

.. note:: Why version 1.4.1?

    six-1.4.1 is the last version of python-six to support Python-2.4.  As
    long as Ansible modules need to run on Python-2.4 we won't be able to
    update the bundled copy of six.

Compile Test
------------

We have travis compiling all modules with various versions of Python to check
that the modules conform to the syntax at those versions.  When you've
ported a module so that its syntax works with Python-3, we need to modify
.travis.yml so that the module is included in the syntax check.  Here's the
relevant section of .travis.yml::

    env:
      global:
        - PY3_EXCLUDE_LIST="cloud/amazon/cloudformation.py
          cloud/amazon/ec2_ami.py
          [...]
          utilities/logic/wait_for.py"

The :envvar:`PY3_EXCLUDE_LIST` environment variable is a blacklist of modules
which should not be tested (because we know that they are older modules which
have not yet been ported to pass the Python-3 syntax checks.  To get another
old module to compile with Python-3, remove the entry for it from the list.
The goal is to have the LIST be empty.
