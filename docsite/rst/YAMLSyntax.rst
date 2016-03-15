YAML Syntax
===========

This page provides a basic overview of correct YAML syntax, which is how Ansible
playbooks (our configuration management language) are expressed.  

We use YAML because it is easier for humans to read and write than other common
data formats like XML or JSON.  Further, there are libraries available in most
programming languages for working with YAML.

You may also wish to read :doc:`playbooks` at the same time to see how this
is used in practice.


YAML Basics
-----------

For Ansible, nearly every YAML file starts with a list.   
Each item in the list is a list of key/value pairs, commonly
called a "hash" or a "dictionary".  So, we need to know how
to write lists and dictionaries in YAML.

There's another small quirk to YAML.  All YAML files (regardless of their association with Ansible or not) can optionally
begin with ``---`` and end with ``...``.  This is part of the YAML format and indicates the start and end of a document.

All members of a list are lines beginning at the same indentation level starting with a ``"- "`` (a dash and a space)::

    ---
    # A list of tasty fruits
    fruits:
        - Apple
        - Orange
        - Strawberry
        - Mango
    ...

A dictionary is represented in a simple ``key: value`` form (the colon must be followed by a space)::

    # An employee record
    martin:
        name: Martin D'vloper
        job: Developer
        skill: Elite

Dictionaries and lists can also be represented in an abbreviated form if you really want to::

    ---
    martin: {name: Martin D'vloper, job: Developer, skill: Elite}
    fruits: ['Apple', 'Orange', 'Strawberry', 'Mango]

.. _truthiness:

Ansible doesn't really use these too much, but you can also specify a boolean value (true/false) in several forms::

    create_key: yes
    needs_agent: no
    knows_oop: True
    likes_emacs: TRUE
    uses_cvs: false


Let's combine what we learned so far in an arbitrary YAML example.
This really has nothing to do with Ansible, but will give you a feel for the format::

    ---
    # An employee record
    name: Martin D'vloper
    job: Developer
    skill: Elite
    employed: True
    foods:
        - Apple
        - Orange
        - Strawberry
        - Mango
    languages:
        ruby: Elite
        python: Elite
        dotnet: Lame

That's all you really need to know about YAML to start writing `Ansible` playbooks.

Gotchas
-------

While YAML is generally friendly, the following is going to result in a YAML syntax error::

    foo: somebody said I should put a colon here: so I did

You will want to quote any hash values using colons, like so::

    foo: "somebody said I should put a colon here: so I did"

And then the colon will be preserved.

Further, Ansible uses "{{ var }}" for variables.  If a value after a colon starts
with a "{", YAML will think it is a dictionary, so you must quote it, like so::

    foo: "{{ variable }}"

The same applies for strings that start or contain any YAML special characters `` [] {} : > | `` .

Boolean conversion is helpful, but this can be a problem when you want a literal `yes` or other boolean values as a string.
In these cases just use quotes::

    non_boolean: "yes"
    other_string: "False"


.. seealso::

   :doc:`playbooks`
       Learn what playbooks can do and how to write/run them.
   `YAMLLint <http://yamllint.com/>`_
       YAML Lint (online) helps you debug YAML syntax if you are having problems
   `Github examples directory <https://github.com/ansible/ansible-examples>`_
       Complete playbook files from the github project source
   `Mailing List <http://groups.google.com/group/ansible-project>`_
       Questions? Help? Ideas?  Stop by the list on Google Groups
   `irc.freenode.net <http://irc.freenode.net>`_
       #ansible IRC chat channel

