.. _interpreter_discovery:

Interpreter Discovery
=====================

Most Ansible modules that execute under a POSIX environment require a Python interpreter on the target host. Unless
configured otherwise, Ansible will attempt to automatically discover a suitable Python interpreter on each target host
the first time a Python module is executed for that host.

The discovery behavior can be controlled for individual hosts and groups by setting the ``ansible_python_interpreter``
inventory variable, or in ``ansible.cfg`` by setting the ``interpreter_python`` key under the ``[defaults]`` section to
one of the following values:

auto_legacy : (default in 2.8)
  Detects the target OS platform, distribution, and version, then looks it up against a table of distribution versions
  known to include a platform Python interpreter (and the path to that interpreter, if present). If an entry is found,
  the looked-up interpreter is used, *except* when ``/usr/bin/python`` is present (in which case a warning is issued and
  ``/usr/bin/python`` is used instead). This exception provides temporary compatibility with previous versions of
  Ansible that always defaulted to ``/usr/bin/python`` (e.g., if other Python dependencies were installed there), but in
  Ansible version 2.12, the looked-up interpreter will be used instead. If a well-known Python is not listed or not
  present for the target's operating system, a list of common Python interpreter paths is searched, and the first one
  found will be used (and a warning issued that future installation of another Python interpreter could alter the one
  chosen).

auto : (future default in 2.12)
  Detects the target OS platform, distribution, and version, then looks it up against a table of distribution versions
  known to include a platform Python interpreter (and the path to that interpreter, if present). If an entry is found,
  the looked-up interpreter is used. If a well-known Python is not listed or not present for the target's operating
  system, a list of common Python interpreter paths is searched, and the first one found will be used (and a warning
  issued that future installation of another Python interpreter could alter the one chosen).

auto_silent
  Same as ``auto``, but does not issue warnings.

(path to a specific Python interpreter)
  Completely disables automatic interpreter discovery; always uses the path specified.
