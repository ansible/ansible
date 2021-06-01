.. _collections_shared_resources:

*************************************
Using shared resources in collections
*************************************

Although developing Ansible modules contained in collections is similar to developing standalone Ansible modules, you use shared resources like documentation fragments and module utilities differently in collections. You can use documentation fragments within and across collections. You can use optional module utilities to support multiple versions of ansible-core in your collection.

.. contents::
   :local:
   :depth: 2

.. _docfragments_collections:

Using documentation fragments in collections
============================================

To include documentation fragments in your collection:

#. Create the documentation fragment: ``plugins/doc_fragments/fragment_name``.

#. Refer to the documentation fragment with its FQCN.

.. code-block:: yaml

   extends_documentation_fragment:
     - kubernetes.core.k8s_name_options
     - kubernetes.core.k8s_auth_options
     - kubernetes.core.k8s_resource_options
     - kubernetes.core.k8s_scale_options

:ref:`module_docs_fragments` covers the basics for documentation fragments. The `kubernetes.core <https://github.com/ansible-collections/kubernetes.core>`_ collection includes a complete example.

If you use FQCN, you can use documentation fragments from one collection in another collection.

.. _optional_module_utils:

Leveraging optional module utilities in collections
===================================================

Optional module utilities let you adopt the latest features from the most recent ansible-core release in your collection-based modules without breaking your collection on older Ansible versions. With optional module utilities, you can leverage the latest features when running against the latest versions, while still providing fallback behaviors when running against older versions.

This implementation, widely used in Python programming, wraps optional imports in conditionals or defensive `try/except` blocks, and implements fallback behaviors for missing imports. Ansible's module payload builder supports these patterns by treating any module_utils import nested in a block (e.g., `if`, `try`) as optional. If the requested import cannot be found during the payload build, it is simply omitted from the target payload and assumed that the importing code will handle its absence at runtime. Missing top-level imports of module_utils packages (imports that are not wrapped in a block statement of any kind) will fail the module payload build, and will not execute on the target.

For example, the `ansible.module_utils.common.respawn` package is only available in Ansible 2.11 and higher. The following module code would fail during the payload build on Ansible 2.10 or earlier (as the requested Python module does not exist, and is not wrapped in a block to signal to the payload builder that it can be omitted from the module payload):

.. code-block:: python

   from ansible.module_utils.common.respawn import respawn_module

By wrapping the import statement in a ``try`` block, the payload builder will omit the Python module if it cannot be located, and assume that the Ansible module will handle it at runtime:

.. code-block:: python

   try:
       from ansible.module_utils.common.respawn import respawn_module
   except ImportError:
       respawn_module = None
   ...
   if needs_respawn:
       if respawn_module:
           respawn_module(target)
       else:
           module.fail_json('respawn is not available in Ansible < 2.11, ensure that foopkg is installed')

The optional import behavior also applies to module_utils imported from collections.

.. seealso::

   :ref:`collections`
       Learn how to install and use collections.
   :ref:`contributing_maintained_collections`
       Guidelines for contributing to selected collections
   `Mailing List <https://groups.google.com/group/ansible-devel>`_
       The development mailing list
   `irc.libera.chat <https://libera.chat/>`_
       #ansible IRC chat channel
