no-main-display
===============

As of Ansible 2.8, ``Display`` should no longer be imported from ``__main__``.

``Display`` is now a singleton and should be utilized like the following::

   from ansible.utils.display import Display
   display = Display()

There is no longer a need to attempt ``from __main__ import display`` inside
a ``try/except`` block.
