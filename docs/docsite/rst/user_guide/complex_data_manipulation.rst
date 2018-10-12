Complex data manipulation
#########################

In many cases you need to do some complex operation with your variables, while Ansible is not recommended as a data processing/manipulation tool, you can use the existing Jinja2 templating in conjunction with the many added ansible filters, lookups and tests to do some very complex transformations.

A quick definition of each type of plugin before we go forward
  - lookups: Mainly used to query 'external data', in Ansible these were the primary part of loops using the `with_<lookup>` construct, but they can be used independantly to return data for processing. They normally returna list due to their primary function in loops as mentioned previouslly. Used with the ``lookup`` or ``query`` Jinja2 operators.
  - filters: used to change/transform data, used mainly with the ``|`` Jinja2 operator.
  - tests: used to validate data, used mainly with the ``is`` Jinja2 operator.


.. _for_loops_or_list_comprehensions:
For loops and/or list comprehensions
====================================

Most programmers are used to using a for loop (or while and others) and list comprehensions to do transformations on lists or lists of objects, Jinja2 has a few filters that provide this functionality: map, select, reject, selectattr, rejectattr

 - map: this is a basic for loop that just allows you to transform every item in a list, using the 'attribute' keyword you can do the transformation based on a attribute of the list element.

 - select/reject: this is a for loop with a conditional, that allows you to create a subset of a list that matches (or not) a condition
 - selectattr/rejectattr: very similar to the above but it uses a specific attribute of the list element for the conditional



Examples
========

.. _keys_from_dict_matching_list:
Extract keys form a dictionary matching elements from a list
------------------------------------------------------------

.. code::

  tasks:
    - debug: msg="{{ chains|map('extract', chains_config)|map(attribute='configs')|flatten|map(attribute='type')|flatten }}"
      vars:
        chains = [1, 2, 3, 4, 5]
        chains_config:
            1:
                foo: bar
                configs:
                    - type: routed
                      version: 0.1
                    - type: bridged
                      version: 0.2
            2:
                foo: baz
                configs:
                    - type: routed
                      version: 1.0
                    - type: bridged
                      version: 1.1
Results in::

    ok: [localhost] => {
        "msg": [
            "routed",
            "bridged",
            "routed",
            "bridged"
        ]
    }

The equivalent pseudo code would be::

    for each chain in chains
        for each config in chains_config[chain]['configs']
            print config['type']
        end for
    end for

