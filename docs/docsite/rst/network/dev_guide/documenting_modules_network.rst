
.. _documenting_modules_network:

*********************************
Documenting new network platforms
*********************************

.. contents::
  :local:

When you create network modules for a new platform, or modify the connections provided by an existing network platform(such as ``network_cli`` and ``httpapi``), you also need to update  the :ref:`settings_by_platform` table and add or modify the Platform Options file for your platform.

You should already have documented each module as described in :ref:`developing_modules_documenting`.

Modifying the platform options table
====================================

The :ref:`settings_by_platform` table is a convenient summary of the connections options provided by each network platform that has modules in Ansible. Add a row for your platform to this table, in alphabetical order.  For example:

.. code-block:: text

    +-------------------+-------------------------+-------------+---------+---------+----------+
    | My OS             | ``myos``                | ✓           | ✓       |         | ✓        |

Ensure that the table stays formatted correctly. That is:

* Each row is inserted in alphabetical order.
* The cell division ``|`` markers line up with the ``+`` markers.
* The check marks appear only for the connection types provided by the network modules.



Adding a platform-specific options section
==========================================

The platform- specific sections are individual ``.rst`` files that provide more detailed information for the users of your network platform modules.   Name your new file ``platform_<name>.rst`` (for example, ``platform_myos.rst``).  The platform name should match the module prefix. See `platform_eos.rst <https://github.com/ansible/ansible/blob/devel/docs/docsite/rst/network/user_guide/platform_eos.rst>`_ and :ref:`eos_platform_options` for an example of the details you should provide in your platform-specific options section.

Your platform-specific section should include the following:

* **Connections available table** - a deeper dive into each connection type, including details on credentials, indirect access, connections settings, and enable mode.
* **How to use each connection type** - with working examples of each connection type.

If your network platform supports SSH connections, also include the following at the bottom of your ``.rst`` file:

.. code-block:: text

    .. include:: shared_snippets/SSH_warning.txt

Adding your new file to the table of contents
=============================================

As a final step, add your new file in alphabetical order in the ``platform_index.rst`` file. You should then build the documentation to verify your additions. See :ref:`community_documentation_contributions` for more details.
