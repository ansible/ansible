.. _templating_now:

The now function: get the current time
======================================

.. versionadded:: 2.8

The ``now()`` Jinja2 function retrieves a Python datetime object or a string representation for the current time.

The ``now()`` function supports 2 arguments:

utc
  Specify ``True`` to get the current time in UTC. Defaults to ``False``.

fmt
  Accepts a `strftime <https://docs.python.org/3/library/datetime.html#strftime-strptime-behavior>`_ string that returns a formatted date time string.