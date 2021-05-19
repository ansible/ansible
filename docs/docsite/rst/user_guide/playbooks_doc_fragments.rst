.. _playbooks_doc_fragments:

*********************
Doc Fragments Plugins
*********************

If you are writing multiple related modules, they may share common documentation, such as authentication details, file mode settings, ``notes:`` or ``seealso:`` entries. Rather than duplicate that information in each module's ``DOCUMENTATION`` block, you can save it once as a doc_fragment plugin and use it in each module's documentation. In Ansible, shared documentation fragments are contained in a ``ModuleDocFragment`` class in `lib/ansible/plugins/doc_fragments/ <https://github.com/ansible/ansible/tree/devel/lib/ansible/plugins/doc_fragments>`_ or the equivalent directory in a collection. To include a documentation fragment, add ``extends_documentation_fragment: FRAGMENT_NAME`` in your module documentation. Use the fully qualified collection name for the FRAGMENT_NAME (for example, ``kubernetes.core.k8s_auth_options``).

Modules should only use items from a doc fragment if the module will implement all of the interface documented there in a manner that behaves the same as the existing modules which import that fragment. The goal is that items imported from the doc fragment will behave identically when used in another module that imports the doc fragment.

By default, only the ``DOCUMENTATION`` property from a doc fragment is inserted into the module documentation. It is possible to define additional properties in the doc fragment in order to import only certain parts of a doc fragment or mix and match as appropriate. If a property is defined in both the doc fragment and the module, the module value overrides the doc fragment.

Here is an example doc fragment named ``example_fragment.py``:

.. code-block:: python

    class ModuleDocFragment(object):
        # Standard documentation
        DOCUMENTATION = r'''
        options:
          # options here
        '''

        # Additional section
        OTHER = r'''
        options:
          # other options here
        '''


To insert the contents of ``OTHER`` in a module:

.. code-block:: yaml+jinja

    extends_documentation_fragment: example_fragment.other

Or use both :

.. code-block:: yaml+jinja

    extends_documentation_fragment:
      - example_fragment
      - example_fragment.other

.. _note:
  * Prior to Ansible 2.8, documentation fragments were kept in ``lib/ansible/utils/module_docs_fragments``.

.. versionadded:: 2.8

Since Ansible 2.8, you can have user-supplied doc_fragments by using a ``doc_fragments`` directory adjacent to play or role, just like any other plugin.

For example, all AWS modules should include:

.. code-block:: yaml+jinja

    extends_documentation_fragment:
    - aws
    - ec2

:ref:`docfragments_collections` describes how to incorporate documentation fragments in a collection.

.. seealso::

   :ref:`working_with_playbooks`
       An introduction to playbooks
   :ref:`playbooks_conditionals`
       Conditional statements in playbooks
   :ref:`playbooks_variables`
       All about variables
   :ref:`playbooks_loops`
       Looping in playbooks
   `User Mailing List <https://groups.google.com/group/ansible-devel>`_
       Have a question?  Stop by the google group!
   `irc.freenode.net <http://irc.freenode.net>`_
       #ansible IRC chat channel
