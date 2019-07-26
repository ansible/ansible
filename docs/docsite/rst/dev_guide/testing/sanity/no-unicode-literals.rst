no-unicode_literals
===================

The use of :code:`from __future__ import unicode_literals` has been deemed an anti-pattern.  The
problems with it are:

* It makes it so one can't jump into the middle of a file and know whether a bare literal string is
  a byte string or text string.  The programmer has to first check the top of the file to see if the
  import is there.
* It removes the ability to define native strings (a string which should be a byte string on python2
  and a text string on python3) via a string literal.
* It makes for more context switching.  A programmer could be reading one file which has
  `unicode_literals` and know that bare string literals are text strings but then switch to another
  file (perhaps tracing program execution into a third party library) and have to switch their
  understanding of what bare string literals are.

