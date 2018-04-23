.. _variable_evaluation:

Variable Evaluation
```````````````````

In general, Ansible evaluates any variables in playbook content at the last
possible second, which means that if you define a data structure that data
structure itself can define variable values within it, and everything “just
works” as you would expect. This also means variable strings can include other
variables inside of those strings. This is known as Lazy Evaluation, which
allows for variables to be defined out of order so long as they are defined
before usage.

::

    vars:
        a: "{{ b }}"
        b: 3


When using an Ansible :ref:`Lookup Plugin`, do note that the value will be
evaluated every time the variable is expanded in a template or in a playbook
unless it is explicitly used with ``set_fact`` which will evaluate and define
var with the result of the Lookup Plugin be stored in the variable, effectively
resulting in a single evaluation of the variable.

::

    - set_fact:
        timestamp_at_eval_time: "{{ lookup('pipe', 'date +%Y-%m-%d-%H-%M') }}"
