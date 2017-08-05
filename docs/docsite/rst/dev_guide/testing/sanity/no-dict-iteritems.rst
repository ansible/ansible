Sanity Tests » no-dict-iteritems
================================

The ``dict.iteritems`` method has been removed in Python 3. There are two recommended alternatives:

.. code-block:: python

    for KEY, VALUE in DICT.items():
       pass

.. code-block:: python

    from ansible.module_utils.six import iteritems

    for KEY, VALUE in iteritems(DICT):
        pass
