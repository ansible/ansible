no-dict-itervalues
==================

The ``dict.itervalues`` method has been removed in Python 3. There are two recommended alternatives:

.. code-block:: python

    for VALUE in DICT.values():
       pass

.. code-block:: python

    from ansible.module_utils.six import itervalues

    for VALUE in itervalues(DICT):
        pass
