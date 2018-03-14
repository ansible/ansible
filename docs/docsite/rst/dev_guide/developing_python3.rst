.. _developing_python_3:

====================
Ansible and Python 3
====================

Ansible is pursuing a strategy of having one code base that runs on both
Python-2 and Python-3 because we want Ansible to be able to manage a wide
variety of machines.  Contributors to Ansible should be aware of the tips in
this document so that they can write code that will run on the same versions
of Python as the rest of Ansible.

Ansible can be divided into three overlapping pieces for the purposes of
porting:

1. Controller-side code.  This is the code which runs on the machine where you
   invoke :command:`/usr/bin/ansible`
2. Modules.  This is the code which Ansible transmits over the wire and
   invokes on the managed machine.
3. module_utils code.  This is code whose primary purpose is to be used by the
   modules to perform tasks.  However, some controller-side code might use
   generic functions from here.

Much of the knowledge of porting code will be usable on all three of these
pieces but there are some special considerations for some of it as well.
Information that is generally applicable to all three places is located in the
controller-side section.

--------------------------------------------
Minimum Version of Python-3.x and Python-2.x
--------------------------------------------

In both controller side and module code, we support Python-3.5 or greater and Python-2.6 or
greater.  Python-3.5 was chosen as a minimum because it is the earliest Python-3 version
adopted as the default Python by a Long Term Support (LTS) Linux distribution (in this case, Ubuntu-16.04).
Previous LTS Linux distributions shipped with a Python-2 version which users can rely upon instead of the 
Python-3 version.

For Python-2, the default is for modules to run on at least Python-2.6.  This allows
users with older distributions that are stuck on Python-2.6 to manage their
machines.  Modules are allowed to drop support for Python-2.6 when one of
their dependent libraries requires a higher version of Python.  This is not an
invitation to add unnecessary dependent libraries in order to force your
module to be usable only with a newer version of Python; instead it is an
acknowledgment that some libraries (for instance, boto3 and docker-py) will
only function with a newer version of Python.

.. note:: Python-2.4 Module-side Support:

    Support for Python-2.4 and Python-2.5 was dropped in Ansible-2.4.  RHEL-5
    (and its rebuilds like CentOS-5) were supported until April of 2017.
    Ansible-2.3 was released in April of 2017 and was the last Ansible release
    to support Python-2.4 on the module-side.

-----------------------------------
Porting Controller Code to Python 3
-----------------------------------

Most of the general tips for porting code to be used on both Python-2 and
Python-3 applies to porting controller code.  The best place to start learning
to port code is `Lennart Regebro's book: Porting to Python 3 <http://python3porting.com/>`_.

The book describes several strategies for porting to Python 3.  The one we're
using is `to support Python-2 and Python-3 from a single code base
<http://python3porting.com/strategies.html#python-2-and-python-3-without-conversion>`_

Controller String Strategy
==========================

Background
----------

One of the most essential things to decide upon for porting code to Python-3
is what string model to use.  Strings can be an array of bytes (like in C) or
they can be an array of text.  Text is what we think of as letters, digits,
numbers, other printable symbols, and a small number of unprintable "symbols"
(control codes).

In Python-2, the two types for these (:class:`str` for bytes and
:class:`unicode` for text) are often used interchangeably.  When dealing only
with ASCII characters, the strings can be combined, compared, and converted
from one type to another automatically.  When non-ASCII characters are
introduced, Python starts throwing exceptions due to not knowing what encoding
the non-ASCII characters should be in.

Python-3 changes this behavior by making the separation between bytes (:class:`bytes`)
and text (:class:`str`) more strict.  Python will throw an exception when
trying to combine and compare the two types.  The programmer has to explicitly
convert from one type to the other to mix values from each.

This change makes it immediately apparent to the programmer when code is
mixing the types inappropriately, rather than working until one of their users
causes an exception by entering non-ASCII input.  However, it forces the
programmer to proactively define a strategy for working with strings in their
program so that they don't mix text and byte strings unintentionally.

Unicode Sandwich
----------------

In controller-side code we use a strategy known as the Unicode Sandwich (named
after Python-2's :class:`unicode` text type).  For Unicode Sandwich we know that
at the border of our code and the outside world (for example, file and network IO,
environment variables, and some library calls) we are going to receive bytes.
We need to transform these bytes into text and use that throughout the
internal portions of our code.  When we have to send those strings back out to
the outside world we first convert the text back into bytes.
To visualize this, imagine a 'sandwich' consisting of a top and bottom layer
of bytes, a layer of conversion between, and all text type in the center.

Common Borders
--------------

This is a partial list of places where we have to convert to and from bytes.
It's not exhaustive but gives you an idea of where to watch for problems.

Reading and writing to files
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In Python-2, reading from files yields bytes.  In Python-3, it can yield text.
To make code that's portable to both we don't make use of Python-3's ability
to yield text but instead do the conversion explicitly ourselves. For example:

.. code-block:: python

    from ansible.module_utils._text import to_text

    with open('filename-with-utf8-data.txt', 'rb') as my_file:
        b_data = my_file.read()
        try:
            data = to_text(b_data, errors='surrogate_or_strict')
        except UnicodeError:
            # Handle the exception gracefully -- usually by displaying a good
            # user-centric error message that can be traced back to this piece
            # of code.
            pass

.. note:: Much of Ansible assumes that all encoded text is UTF-8.  At some
    point, if there is demand for other encodings we may change that, but for
    now it is safe to assume that bytes are UTF-8.

Writing to files is the opposite process:

.. code-block:: python

    from ansible.module_utils._text import to_bytes

    with open('filename.txt', 'wb') as my_file:
        my_file.write(to_bytes(some_text_string))

Note that we don't have to catch :exc:`UnicodeError` here because we're
transforming to UTF-8 and all text strings in Python can be transformed back
to UTF-8.

Filesystem Interaction
~~~~~~~~~~~~~~~~~~~~~~

Dealing with filenames often involves dropping back to bytes because on UNIX-like
systems filenames are bytes.  On Python-2, if we pass a text string to these
functions, the text string will be converted to a byte string inside of the
function and a traceback will occur if non-ASCII characters are present.  In
Python-3, a traceback will only occur if the text string can't be decoded in
the current locale, but it's still good to be explicit and have code which
works on both versions:

.. code-block:: python

    import os.path

    from ansible.module_utils._text import to_bytes

    filename = u'/var/tmp/くらとみ.txt'
    f = open(to_bytes(filename), 'wb')
    mtime = os.path.getmtime(to_bytes(filename))
    b_filename = os.path.expandvars(to_bytes(filename))
    if os.path.exists(to_bytes(filename)):
        pass

When you are only manipulating a filename as a string without talking to the
filesystem (or a C library which talks to the filesystem) you can often get
away without converting to bytes:

.. code-block:: python

    import os.path

    os.path.join(u'/var/tmp/café', u'くらとみ')
    os.path.split(u'/var/tmp/café/くらとみ')

On the other hand, if the code needs to manipulate the filename and also talk
to the filesystem, it can be more convenient to transform to bytes right away
and manipulate in bytes.

.. warning:: Make sure all variables passed to a function are the same type.
    If you're working with something like :func:`os.path.join` which takes
    multiple strings and uses them in combination, you need to make sure that
    all the types are the same (either all bytes or all text).  Mixing
    bytes and text will cause tracebacks.

Interacting with Other Programs
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Interacting with other programs goes through the operating system and
C libraries and operates on things that the UNIX kernel defines.  These
interfaces are all byte-oriented so the Python interface is byte oriented as
well.  On both Python-2 and Python-3, byte strings should be given to Python's
subprocess library and byte strings should be expected back from it.

One of the main places in Ansible's controller code that we interact with
other programs is the connection plugins' ``exec_command`` methods.  These
methods transform any text strings they receive in the command (and arguments
to the command) to execute into bytes and return stdout and stderr as byte strings 
Higher level functions (like action plugins' ``_low_level_execute_command``)
transform the output into text strings.

Tips, tricks, and idioms to adopt
=================================

Forwards Compatibility Boilerplate
----------------------------------

Use the following boilerplate code at the top of all controller-side modules
to make certain constructs act the same way on Python-2 and Python-3:

.. code-block:: python

    # Make coding more python3-ish
    from __future__ import (absolute_import, division, print_function)
    __metaclass__ = type

``__metaclass__ = type`` makes all classes defined in the file into new-style
classes without explicitly inheriting from :class:`object`.

The ``__future__`` imports do the following:

:absolute_import: Makes imports look in :attr:`sys.path` for the modules being
    imported, skipping the directory in which the module doing the importing
    lives.  If the code wants to use the directory in which the module doing
    the importing, there's a new dot notation to do so.
:division: Makes division of integers always return a float.  If you need to
   find the quotient use ``x // y`` instead of ``x / y``.
:print_function: Changes :func:`print` from a keyword into a function.

.. seealso::
    * `PEP 0328: Absolute Imports <https://www.python.org/dev/peps/pep-0328/#guido-s-decision>`_
    * `PEP 0238: Division <https://www.python.org/dev/peps/pep-0238>`_
    * `PEP 3105: Print function <https://www.python.org/dev/peps/pep-3105>`_

Prefix byte strings with "b\_"
------------------------------

Since mixing text and bytes types leads to tracebacks we want to be clear
about what variables hold text and what variables hold bytes.  We do this by
prefixing any variable holding bytes with ``b_``.  For instance:

.. code-block:: python

    filename = u'/var/tmp/café.txt'
    b_filename = to_bytes(filename)
    with open(b_filename) as f:
        data = f.read()

We do not prefix the text strings instead because we only operate
on byte strings at the borders, so there are fewer variables that need bytes
than text.

Bundled six
-----------

The third-party `python-six <https://pythonhosted.org/six/>`_ library exists
to help projects create code that runs on both Python-2 and Python-3.  Ansible
includes a version of the library in module_utils so that other modules can use it
without requiring that it is installed on the remote system.  To make use of
it, import it like this:

.. code-block:: python

    from ansible.module_utils import six

.. note:: Ansible can also use a system copy of six

    Ansible will use a system copy of six if the system copy is a later
    version than the one Ansible bundles.

Exceptions
----------

In order for code to function on Python-2.6+ and Python-3, use the
new exception-catching syntax which uses the ``as`` keyword:

.. code-block:: python

    try:
        a = 2/0
    except ValueError as e:
        module.fail_json(msg="Tried to divide by zero: %s" % e)

Do **not** use the following syntax as it will fail on every version of Python-3:

.. This code block won't highlight because python2 isn't recognized. This is necessary to pass tests under python 3.
.. code-block:: none

    try:
        a = 2/0
    except ValueError, e:
        module.fail_json(msg="Tried to divide by zero: %s" % e)

Octal numbers
-------------

In Python-2.x, octal literals could be specified as ``0755``.  In Python-3,
octals must be specified as ``0o755``.

String formatting
-----------------

str.format() compatibility
~~~~~~~~~~~~~~~~~~~~~~~~~~

Starting in Python-2.6, strings gained a method called ``format()`` to put
strings together.  However, one commonly used feature of ``format()`` wasn't
added until Python-2.7, so you need to remember not to use it in Ansible code:

.. code-block:: python

    # Does not work in Python-2.6!
    new_string = "Dear {}, Welcome to {}".format(username, location)

    # Use this instead
    new_string = "Dear {0}, Welcome to {1}".format(username, location)

Both of the format strings above map positional arguments of the ``format()``
method into the string.  However, the first version doesn't work in
Python-2.6.  Always remember to put numbers into the placeholders so the code
is compatible with Python-2.6.

.. seealso::
    Python documentation on `format strings <https://docs.python.org/2/library/string.html#formatstrings>`_


Use percent format with byte strings
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In Python-3.x, byte strings do not have a ``format()`` method.  However, it
does have support for the older, percent-formatting.

.. code-block:: python

    b_command_line = b'ansible-playbook --become-user %s -K %s' % (user, playbook_file)

.. note:: Percent formatting added in Python-3.5

    Percent formatting of byte strings was added back into Python3 in 3.5.
    This isn't a problem for us because Python-3.5 is our minimum version.
    However, if you happen to be testing Ansible code with Python-3.4 or
    earlier, you will find that the byte string formatting here won't work.
    Upgrade to Python-3.5 to test.

.. seealso::
    Python documentation on `percent formatting <https://docs.python.org/2/library/stdtypes.html#string-formatting>`_

---------------------------
Porting Modules to Python 3
---------------------------

Ansible modules are slightly harder to port than normal code from other
projects. A lot of mocking has to go into unit testing an Ansible module so
it's harder to test that your porting has fixed everything or to to make sure
that later commits haven't regressed the Python-3 support.

Module String Strategy
======================

There are a large number of modules in Ansible.  Most of those are maintained
by the Ansible community at large, not by a centralized team.  To make life
easier on them, it was decided not to break backwards compatibility by
mandating that all strings inside of modules are text and converting between
text and bytes at the borders; instead, we're using a native string strategy
for now.

Native strings refer to the type that Python uses when you specify a bare
string literal:

.. code-block:: python

    "This is a native string"

In Python-2, these are byte strings.  In Python-3 these are text strings.  The
module_utils shipped with Ansible attempts to accept native strings as input
to its functions and emit native strings as their output.  Modules should be
coded to expect bytes on Python-2 and text on Python-3.

Tips, tricks, and idioms to adopt
=================================

Python-2.4 Compatible Exception Syntax
--------------------------------------

Until Ansible-2.4, modules needed to be compatible with Python-2.4 as
well.  Python-2.4 did not understand the new exception-catching syntax so
we had to write a compatibility function that could work with both
Python-2 and Python-3.  You may still see this used in some modules:

.. code-block:: python

    from ansible.module_utils.pycompat24 import get_exception

    try:
        a = 2/0
    except ValueError:
        e = get_exception()
        module.fail_json(msg="Tried to divide by zero: %s" % e)

Unless a change is going to be backported to Ansible-2.3, you should not
have to use this in new code.

Python 2.4 octal workaround
---------------------------

Before Ansible-2.4, modules had to be compatible with Python-2.4.
Python-2.4 did not understand the new syntax for octal literals so we used
the following workaround to specify octal values:

.. code-block:: python

    # Can't use 0755 on Python-3 and can't use 0o755 on Python-2.4
    EXECUTABLE_PERMS = int('0755', 8)

Unless a change is going to be backported to Ansible-2.3, you should not
have to use this in new code.

-------------------------------------
Porting module_utils code to Python 3
-------------------------------------

module_utils code is largely like module code.  However, some pieces of it are
used by the controller as well.  Because of this, it needs to be usable with
the controller's assumptions.  This is most notable in the string strategy.

Module_utils String Strategy
============================

Module_utils **must** use the Native String Strategy.  Functions in
module_utils receive either text strings or byte strings and may emit either
the same type as they were given or the native string for the Python version
they are run on depending on which makes the most sense for that function.
Functions which return strings **must** document whether they return text,
byte, or native strings. Module-utils functions are therefore often very
defensive in nature, converting from potential text or bytes at the
beginning of a function and converting to the native string type at the end.
