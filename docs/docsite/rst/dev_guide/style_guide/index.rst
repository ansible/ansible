.. _style_guide:

*******************
Ansible style guide
*******************

Welcome to the Ansible style guide!
To create clear, concise, consistent, useful materials on docs.ansible.com, follow these guidelines:

.. contents::
   :local:

Linguistic guidelines
=====================

We want the Ansible documentation to be:

* clear
* direct
* conversational
* easy to translate

We want reading the docs to feel like having an experienced, friendly colleague
explain how Ansible works.

Stylistic cheat-sheet
---------------------

This cheat-sheet illustrates a few rules that help achieve the "Ansible tone":

+-------------------------------+------------------------------+----------------------------------------+
| Rule                          | Good example                 | Bad example                            |
+===============================+==============================+========================================+
| Use active voice              | You can run a task by        | A task can be run by                   |
+-------------------------------+------------------------------+----------------------------------------+
| Use the present tense         | This command creates a       | This command will create a             |
+-------------------------------+------------------------------+----------------------------------------+
| Address the reader            | As you expand your inventory | When the number of managed nodes grows |
+-------------------------------+------------------------------+----------------------------------------+
| Use standard English          | Return to this page          | Hop back to this page                  |
+-------------------------------+------------------------------+----------------------------------------+
| Use American English          | The color of the output      | The colour of the output               |
+-------------------------------+------------------------------+----------------------------------------+

Header case
-----------

Headers should be written in sentence case. For example, this section's title is
``Header case``, not ``Header Case`` or ``HEADER CASE``.


Avoid using Latin phrases
-------------------------

Latin words and phrases like ``e.g.`` or ``etc.``
are easily understood by English speakers.
They may be harder to understand for others and are also tricky for automated translation.

Use the following English terms in place of Latin terms or abbreviations: 

+-------------------------------+------------------------------+
| Latin                         | English                      | 
+===============================+==============================+
| i.e                           | in other words               | 
+-------------------------------+------------------------------+
| e.g.                          | for example                  |
+-------------------------------+------------------------------+
| etc                           | and so on                    |
+-------------------------------+------------------------------+
| via                           | by/ through                  |
+-------------------------------+------------------------------+
| vs./versus                    | rather than/against          |
+-------------------------------+------------------------------+


reStructuredText guidelines
===========================

The Ansible documentation is written in reStructuredText and processed by Sphinx.
We follow these technical or mechanical guidelines on all rST pages:

Header notation
---------------

`Section headers in reStructuredText <https://www.sphinx-doc.org/en/master/usage/restructuredtext/basics.html#sections>`_
can use a variety of notations.
Sphinx will 'learn on the fly' when creating a hierarchy of headers.
To make our documents easy to read and to edit, we follow a standard set of header notations.
We use:

* ``###`` with overline, for parts:

.. code-block:: rst

      ###############
      Developer guide
      ###############

* ``***`` with overline, for chapters:

.. code-block:: rst

      *******************
      Ansible style guide
      *******************

* ``===`` for sections:

.. code-block:: rst

      Mechanical guidelines
      =====================

* ``---`` for subsections:

.. code-block:: rst

      Internal navigation
      -------------------

* ``^^^`` for sub-subsections:

.. code-block:: rst

      Adding anchors
      ^^^^^^^^^^^^^^

* ``"""`` for paragraphs:

.. code-block:: rst

      Paragraph that needs a title
      """"""""""""""""""""""""""""


Internal navigation
-------------------

`Anchors (also called labels) and links <https://www.sphinx-doc.org/en/master/usage/restructuredtext/roles.html#ref-role>`_
work together to help users find related content.
Local tables of contents also help users navigate quickly to the information they need.
All internal links should use the ``:ref:`` syntax.
Every page should have at least one anchor to support internal ``:ref:`` links.
Long pages, or pages with multiple levels of headers, can also include a local TOC.

Adding anchors
^^^^^^^^^^^^^^

* Include at least one anchor on every page
* Place the main anchor above the main header
* If the file has a unique title, use that for the main page anchor::

   .. _unique_page::

* You may also add anchors elsewhere on the page

Adding internal links
^^^^^^^^^^^^^^^^^^^^^

* All internal links must use ``:ref:`` syntax. These links both point to the anchor defined above:

.. code-block:: rst

   :ref:`unique_page`
   :ref:`this page <unique_page>`

The second example adds custom text for the link.

Adding links to modules and plugins
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

* Module links use the module name followed by ``_module`` for the anchor.
* Plugin links use the plugin name followed by the plugin type. For example, :ref:`enable become plugin <enable_become>`).

.. code-block:: rst

   :ref:`this module <this_module>``
   :ref:`that connection plugin <that_connection>`

Adding local TOCs
^^^^^^^^^^^^^^^^^

The page you're reading includes a `local TOC <http://docutils.sourceforge.net/docs/ref/rst/directives.html#table-of-contents>`_.
If you include a local TOC:

* place it below, not above, the main heading and (optionally) introductory text
* use the ``:local:`` directive so the page's main header is not included
* do not include a title

The syntax is:

.. code-block:: rst

   .. contents::
      :local:

More resources
==============

These pages offer more help with grammatical, stylistic, and technical rules for documentation.

.. toctree::
  :maxdepth: 1

  basic_rules
  voice_style
  trademarks
  grammar_punctuation
  spelling_word_choice
  resources

.. seealso::

   :ref:`community_documentation_contributions`
       How to contribute to the Ansible documentation
   :ref:`testing_documentation_locally`
       How to build the Ansible documentation
   `irc.freenode.net <http://irc.freenode.net>`_
       #ansible-docs IRC chat channel
