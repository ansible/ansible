.. _dict2items-example-with-group:

Using ``dict2items`` in Loops with the ``group`` Module
-------------------------------------------------------

When looping over dictionaries that contain structured data (for example, group names and GIDs),
you can use the ``dict2items`` filter to convert the dictionary into a list of key–value pairs.

Each loop item will then have two attributes: ``item.key`` and ``item.value``.
If ``item.value`` itself is a dictionary, access its fields using dot notation.

**Example:**

.. code-block:: yaml

    - name: Add groups using dict2items
      hosts: all
      tasks:
        - name: Create groups from a dictionary
          ansible.builtin.group:
            name: "{{ item.key }}"
            gid: "{{ item.value.gid }}"
            state: present
          loop: "{{ global_groups | dict2items }}"

**Incorrect usage (common mistake):**

.. code-block:: yaml

    gid: "{{ item.gid }}"   # ❌ This fails because item.gid does not exist

This clarification follows feedback from issue #85897.
