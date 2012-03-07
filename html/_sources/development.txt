Development
===========

Tools
-----

Taboot uses what is becoming a pretty standard and a quite simple
toolset.


Required Tools
``````````````
 #. `python <http://www.python.org>`_ - The python programming language
 #. `distutils <http://docs.python.org/lib/module-distutils.html>`_ - Python building and packaging library
 #. `git <http://git.or.cz/>`_ - Source code management 
 #. `Func <https://fedorahosted.org/func/>`_ - The Fedora Unified Network Controller
 #. `an <http://www.vim.org>`_ `editor <http://www.gnu.org/software/emacs/>`_ or `ide <http://pida.co.uk/>`_ `that <http://scribes.sourceforge.net/>`_ doesn't suck



Optional Tools
``````````````
These should be available via your package manager:

 #. `rpm-build <http://www.rpm.org/max-rpm-snapshot/rpmbuild.8.html>`_ - Should be packaged in your RPM distribution
 #. `pep8 <https://github.com/jcrocholl/pep8>`_ - Check your patches for pep8 compliance with ``make pep8``


Source
------
You can clone the repo via :program:`git` through the following command:::

   $ git clone git://git.fedorahosted.org/Taboot.git


:pep:`0008` should be followed. This outlines the highlights that we
require above and beyond. Your code must follow this (or note why it
can't) before patches will be accepted.

 * global variables should be in ALLCAPPS
 * attributes should be all lowercase
 * classes should be ``CamelCased``, filenames should be ``lowercase``.
 * functions and methods should be lowercase with spaces replaced with _'s::

          def a_test_method(self):
              pass

 * classes should subclass ``object`` unless it subclasses a different object::

          class Person(object):
              pass

          class Steve(Person):
              pass

 * 4 spaces per indent level
 * max length is 79 chars.
 * single quotes preferred over double quotes.
 * avoid ``from x import *`` imports unless a must use
 * modules, functions, classes, and methods all must have docstrings - doc strings should be descriptive of what objects, functions, and methods do
 * document any potentially confusing sections of code
 * functions and methods should be broken down in such a way as to be easily understood and self contained
 * use descriptive variable names, only use things like x, y, etc.. when doing integer loops and even then see if you can use more descriptive names

.. note::
   The ``Makefile`` included in the root of the source distribution
   includes a target called ``pep8``. Run ``make pep8`` to
   automatically scan the ``taboot/`` subdirectory for violations.



Git
---

The best way to develop on Taboot is to branch feature sets. For
instance, if you were to add xml deserialization you would want to
branch locally and work on that branch.::

   $  git branch
 * master
   $ git status
   # On branch master
   nothing to commit (working directory clean)
   $ git branch xmldeserialization
   $ git checkout xmldeserialization

Now we pretend you are all finished and have done at least one commit to the xmldeserialization branch.::


   $ git-format-patch master
   0001-created-initial-classes.patch
   0002-added-in-documentation.patch
   $


You now have patch sets which you can send in for perusal and
acceptance. Open a new ticket in our issue tracker or attach them to
an existing ticket.
