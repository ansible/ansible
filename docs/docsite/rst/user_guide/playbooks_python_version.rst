.. _pb-py-compat:

********************
Python3 in templates
********************

Ansible uses Jinja2 to take advantage of Python data types and standard functions in templates and variables.
You can use these data types and standard functions to perform a rich set of operations on your data. However,
if you use templates, you must be aware of differences between Python versions.

These topics help you design templates that work on both Python2 and Python3. They might also help if you are upgrading from Python2 to Python3. Upgrading within Python2 or Python3 does not usually introduce changes that affect Jinja2 templates.

.. _pb-py-compat-dict-views:

Dictionary views
================

In Python2, the :meth:`dict.keys`, :meth:`dict.values`, and :meth:`dict.items`
methods return a list.  Jinja2 returns that to Ansible via a string
representation that Ansible can turn back into a list.

In Python3, those methods return a :ref:`dictionary view <python3:dict-views>` object. The
string representation that Jinja2 returns for dictionary views cannot be parsed back
into a list by Ansible.  It is, however, easy to make this portable by
using the :func:`list <jinja2:jinja-filters.list>` filter whenever using :meth:`dict.keys`,
:meth:`dict.values`, or :meth:`dict.items`.

.. code-block:: yaml+jinja

    vars:
      hosts:
        testhost1: 127.0.0.2
        testhost2: 127.0.0.3
    tasks:
      - debug:
          msg: '{{ item }}'
        # Only works with Python 2
        #loop: "{{ hosts.keys() }}"
        # Works with both Python 2 and Python 3
        loop: "{{ hosts.keys() | list }}"

.. _pb-py-compat-iteritems:

dict.iteritems()
================

Python2 dictionaries have :meth:`~dict.iterkeys`, :meth:`~dict.itervalues`, and :meth:`~dict.iteritems` methods.

Python3 dictionaries do not have these methods. Use :meth:`dict.keys`, :meth:`dict.values`, and :meth:`dict.items` to make your playbooks and templates compatible with both Python2 and Python3.

.. code-block:: yaml+jinja

    vars:
      hosts:
        testhost1: 127.0.0.2
        testhost2: 127.0.0.3
    tasks:
      - debug:
          msg: '{{ item }}'
        # Only works with Python 2
        #loop: "{{ hosts.iteritems() }}"
        # Works with both Python 2 and Python 3
        loop: "{{ hosts.items() | list }}"

.. seealso::
    * The :ref:`pb-py-compat-dict-views` entry for information on
      why the :func:`list filter <jinja2:jinja-filters.list>` is necessary
      here.
