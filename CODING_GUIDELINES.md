Coding Guidelines
=================

Hi!  Thanks for interest in contributing to Ansible.

Here are some guidelines for contributing code.  The purpose of this document are to establish what we're looking for in code contributions, and to make sure
new contributions know some of the conventions that we've been using.

We don't think much of this should be too strange to readers familiar with contributing to Python projects, though it helps if we all get on the same page.

Language
========

  * While not all components of Ansible must be in Python, core contributions to the Ansible repo must be written in Python.  This is to maximize the ability of everyone to contribute.
  * If you want to write non-Python ansible modules or inventory scripts, that's fine, but they are not going to get merged in most likely.  Sorry!!  

PEP 8 and basic style checks
===========================

  * [PEP 8](https://www.python.org/dev/peps/pep-0008/) is a great Python style guide, which you should read.
  * PEP 8 must not be strictly followed in all aspects, but most of it is good advice
  * In particular, we don't really care about line lengths.  Buy a bigger monitor!
  * To run checks for things we care about, use [ansible-test](http://docs.ansible.com/ansible/dev_guide/testing_pep8.html#running-locally).
  * Similarly, additional checks can be made with "make pyflakes"
  * There is no need to submit code changes for PEP 8 and pyflakes fixes, as these break attribution history.  Project leadership will make these periodically.
  * Do not submit pull requests that simply adjust whitespace in the code

Testing
=======

  * Much of ansible's testing needs are in integration, not unit tests.  Add module tests there.
  * That being said, there are unit tests too!
  * Code written must absolutely pass tests (i.e. "make tests")
  * You should anticipate any error paths in your code and test down those error paths.
  * Additions to tests for core code is welcome, but not always possible.  Be sure things are at least well tested manually in that case.

Whitespace
==========

  * Four space indent is strictly required
  * Include meaningful whitespace between lines of code

Shebang Lines
=============
 
  * /usr/bin/scripts should start with '/usr/bin/env python'
  * module code should still use '/usr/bin/python' as this is replaced automatically by 'ansible_python_interpreter', see the FAQ in the docs for more info.

Comments
========

  * Readability is one of the most important goals for this project
  * Comment any non-trivial code where someone might not know why you are doing something in a particular way
  * Though if something should be commented, that's often a sign someone should write a function
  * All new functions must have a basic docstring comment
  * Commenting above a line is preferable to commenting at the end of a line

Classes
=======

  * With the exception of module code (where inline is better), it is desirable to see classes in their own files.
  * Classes should generally not cause side effects as soon as they are instantiated, move meaningful behavior to methods rather than constructors.
 
Functions and Methods
=====================

  * In general, functions should not be 'too long' and should describe a meaningful amount of work
  * When code gets too nested, that's usually the sign the loop body could benefit from being a function
  * Parts of our existing code are not the best examples of this at times. 
  * Functions should have names that describe what they do, along with docstrings
  * Functions should be named with_underscores
  * "Don't repeat yourself" is generally a good philosophy

Variables
=========

  * Use descriptive variable names instead of variables like 'x', unless x is a obvious loop index
  * Ansible python code uses identifiers like 'ClassesLikeThis and variables_like_this
  * Module parameters should also use_underscores and not runtogether

Module Security
===============

  * Modules must take steps to avoid passing user input from the shell and always check return codes
  * always use module.run_command instead of subprocess or Popen or os.system -- this is mandatory
  * if you use need the shell you must pass use_unsafe_shell=True to module.run_command
  * if you do not need the shell, avoid using the shell
  * any variables that can come from the user input with use_unsafe_shell=True must be wrapped by pipes.quote(x)
  * downloads of https:// resource urls must import module_utils.urls and use the fetch_url method

Misc Preferences
================

Use the dict constructor where possible when allocating dictionaries:

    # not this:
    foo = {
       'a' : 12,
       'b' : 34
    }

    # this:
    foo = dict(
       a=12,
       b=34,
    )

Do not line up variables

    # not this
    a        = 12
    foosball = 34
    xyz      = 'dog'

    # this
    a = 12
    foosball = 34
    xyz = 'dog'

Don't use line continuations:

    # no
    if (this_is_a_very_long_line and foo and \
       i_am_going_to_continue_it):
          bar()

    # better:
    if (this_is_a_very_long_line and foo and i_am_going_to_continue_it):
       bar()

Spacing:

    # no
    x = [1,2,3]

    # no
    x = [ 1, 2, 3 ]

    # yes
    x = [1, 2, 3]

Spacing continued:

    # no
    x=foo(12)

    # no
    x = foo( 12 )

    # yes
    x = foo(12)

Licenses
========

Every file should have a license header, including the copyright of the original author.  Major additions to the module are allowed
to add an additional copyright line, and this is especially true of rewrites, but original authorship copyright messages should be preserved.

All contributions to the core repo should preserve original licenses and new contributions must include the GPLv3 header.

Module Documentation
====================

All module pull requests must include a DOCUMENTATION docstring (YAML format, 
see other modules for examples) as well as an EXAMPLES docstring, which is free form.  

When adding new modules, any new parameter must have a "version_added" attribute.  
When submitting a new module, the module should have a "version_added" attribute in the 
pull request as well, set to the current development version.

Be sure to check grammar and spelling.

It's frequently the case that modules get submitted with YAML that isn't valid, 
so you can run "make webdocs" from the checkout to preview your module's documentation. 
If it fails to build, take a look at your DOCUMENTATION string 
or you might have a Python syntax error in there too.

Python Imports
==============

To make it clear what a module is importing, imports should not be sprinkled throughout the code. 

Python Imports should happen at the top of the file, exempting code from module_utils.

When a conditional runtime import is required, do so something like this instead:

    HAS_FOO = False
    try:
       import foo
       HAS_FOO = True
    except ImportError:
       pass

    ...

    if not HAS_FOO:
       raise Exception("the foo library is required")

This makes it clear what optional dependencies are but allows this to be deferred until runtime.   In the case of module code, the raising of the Exception will be replaced
with a "module.exit_json" call.

Exceptions
==========

In the main body of the code, use typed exceptions where possible:
    
    # not this
    raise Exception("panic!")

    # this
    from ansible import errors
    ...
    raise errors.AnsibleError("panic!")

Similarly, exception checking should be fine grained:

    # not this
    try:
       foo()
    except:
       bar()

    # but this
    try:
       foo()
    except SomeTypedException:
       bar()

List Comprehensions
===================

In general list comprehensions are always preferred to map() and filter() calls.

However, they can be abused.  Optimize for readability, and avoid nesting them too deeply.

Regexes
=======

There is a time and place for them, but here's an illustrative joke.

"A developer had a problem, and used a regular expression to solve it.  Now the developer had two problems".

Often regexes are difficult to maintain, and a trusty call to other string operations can be a great solution, faster,
and more readable.

File Conventions
================

If a piece of code looks for a named YAML file in a directory, it should assume it can take no extension, or an extension of '.yml' or '.yaml'.
This should be true against all code that loads files.

Any code that uses directories should consider the possibility that the directory may be symlink.

New Ansible language parameters
===============================

If adding a new parameter, like 'can_fizzbuzz: True/False' be sure the value of the parameter is templated somewhere in the Runner code, as if anything can be parameterized in Ansible,
there is a user that will try to parameterize it.

String Find
===========

Use 'in':

    # not this:
    if x.find('foo') != -1:

    # this: 
    if 'foo' in x:

String checks
=============

To test if something is a string, consider that it may be unicode.

    # no
    if type(x) == str:

    # yes
    from ansible.module_utils.six import string_types
    if isinstance(x, string_types):

Cleverness
==========

Ansible's code is intended to be read by as many people as possible, so we don't particularly encourage clever or heavily idiomatic code.

In particular, metaclasses are probably not appropriate, however entertaining they may be to add.

Git Practices
=============

Pull requests cannot be accepted that contain merge commits.

Always do "git pull --rebase" and "git rebase" vs "git pull" or "git merge".

Always create a new branch for each pull request to avoid intertwingling different features or fixes on the same branch.

   
Python Version Compliance
=========================

All code in Ansible core must support a minimum version of Python 2.6.

Module code must support a minimum of Python 2.4, with occasional exception for modules that require code that themselves require 2.6 and later.

A quick reminder is that list comprehensions in Python 2.4 are not as fully fleshed out, there are no 'dict' comprehensions, and there is no 'with' statement.
But otherwise it's pretty much all the same.

The End
=======

This was not meant to be a scary document, so we hope it wasn't, but we also hope this helps you write code that is easier to maintain by others in the future.
If you have questions about this document, please ask on the ansible-devel mailing list.

Thank you!
