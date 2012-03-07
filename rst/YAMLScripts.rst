YAML Scripts
============

This page provides a basic overview of correct YAML syntax.


YAML Basics
-----------

For `ansible`, every YAML script must be a list at it's root-most
element. Each item in the list is a dictionary. These dictionaries
represent all the options you can use to write a `ansible` script. In
addition, all YAML files (regardless of their association with
`ansible` or not) should start with ``---``.

In YAML a list can be represented in two ways. In one way all members
of a list are lines beginning at the same indentation level starting
with a ``-`` character::

    ---
    # A list of tasty fruits
    - Apple
    - Orange
    - Strawberry
    - Mango

In the second way a list is represented as comma separated elements
surrounded by square brackets. Newlines are permitted between
elements::

    ---
    # A list of tasty fruits
    [apple, orange, banana, mango]

A dictionary is represented in a simple ``key:`` and ``value`` form::

    ---
    # An employee record
    name: John Eckersberg
    job: Developer
    skill: Elite

Like lists, dictionaries can be represented in an abbreviated form::

    ---
    # An employee record
    {name: John Eckersberg, job: Developer, skill: Elite}

.. _truthiness:

You can specify a boolean value (true/false) in several forms::

    ---
    knows_oop: True
    likes_emacs: TRUE
    uses_cvs: false

Finally, you can combine these data structures::

    ---
    # An employee record
    name: John Eckersberg
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

That's all you really need to know about YAML to get started writing
`Ansible` scripts.

.. seealso::

   `YAMLLint <http://yamllint.com/>`_
       YAML Lint gets the lint out of your YAML
