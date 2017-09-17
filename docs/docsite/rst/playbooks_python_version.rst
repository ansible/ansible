.. _pb-py-compat:

Python Version and Templating
=============================

Jinja2 templates leverage Python data types and standard functions.  This
makes for a rich set of operations that can be performed on data.  However,
this also means that certain specifics of the underlying Python becomes
visible to template authors.  Since Ansible playbooks use Jinja2 for templates
and variables, this means that playbook authors need to be aware of these
specifics as well.

Unless otherwise noted, these differences are only of interest when running
Ansible in Python2 versus Python3.  Changes within Python2 and Python3 are
generally small enough that they are not visible at the jinja2 level.

.. _pb-py-compat-dict-views:

Dictionary Views
----------------

In Python2, the :meth:`dict.keys`, :meth:`dict.values`, and :meth:`dict.items`
methods returns a list.  Jinja2 returns that to Ansible via a string
representation that Ansible can turn back into a list.  In Python3, those
methods return a :ref:`dictionary view <python3:dict-views>` object.  The
string representation that Jinja2 returns for dictionary views cannot be parsed back 
into a list by Ansible.  It is, however, easy to make this portable by
using the :func:`list <jinja2:list>` filter whenever using :meth:`dict.keys`,
:meth:`dict.values`, or :meth:`dict.items`::

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
----------------

In Python2, dictionaries have :meth:`~dict.iterkeys`,
:meth:`~dict.itervalues`, and :meth:`~dict.iteritems` methods.  These methods
have been removed in Python3.  Playbooks and Jinja2 templates should use
:meth:`dict.keys`, :meth:`dict.values`, and :meth:`dict.items` in order to be
compatible with both Python2 and Python3::

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
      why the :func:`list filter <jinja2:list>` is necessary
      here.
