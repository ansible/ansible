.. _authorized_key:

authorized_key
``````````````

.. versionadded:: 0.5

Adds or removes an authorized key for a user from a remote host.

+--------------------+----------+---------+----------------------------------------------------------------------------+
| parameter          | required | default | comments                                                                   |
+====================+==========+=========+============================================================================+
| user               | yes      |         | Name of the user who should have access to the remote host                 |
+--------------------+----------+---------+----------------------------------------------------------------------------+
| key                | yes      |         | the SSH public key, as a string                                            |
+--------------------+----------+---------+----------------------------------------------------------------------------+
| state              | no       | present | whether the given key should or should not be in the file                  |
+--------------------+----------+---------+----------------------------------------------------------------------------+

Example action from Ansible :doc:`playbooks`::

    authorized_key user=charlie key="ssh-dss ASDF1234L+8BTwaRYr/rycsBF1D8e5pTxEsXHQs4iq+mZdyWqlW++L6pMiam1A8yweP+rKtgjK2httVS6GigVsuWWfOd7/sdWippefq74nppVUELHPKkaIOjJNN1zUHFoL/YMwAAAEBALnAsQN10TNGsRDe5arBsW8cTOjqLyYBcIqgPYTZW8zENErFxt7ij3fW3Jh/sCpnmy8rkS7FyK8ULX0PEy/2yDx8/5rXgMIICbRH/XaBy9Ud5bRBFVkEDu/r+rXP33wFPHjWjwvHAtfci1NRBAudQI/98DbcGQw5HmE89CjgZRo5ktkC5yu/8agEPocVjdHyZr7PaHfxZGUDGKtGRL2QzRYukCmWo1cZbMBHcI5FzImvTHS9/8B3SATjXMPgbfBuEeBwuBK5EjL+CtHY5bWs9kmYjmeo0KfUMH8hY4MAXDoKhQ7DhBPIrcjS5jPtoGxIREZjba67r6/P2XKXaCZH6Fc= charlie@example.org 2011-01-17"
