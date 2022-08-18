.. _inventory_guide_index:

############################
Building Ansible inventories
############################

.. note::

    **Making Open Source More Inclusive**

    Red Hat is committed to replacing problematic language in our code, documentation, and web properties. We are beginning with these four terms: master, slave, blacklist, and whitelist. We ask that you open an issue or pull request if you come upon a term that we have missed. For more details, see `our CTO Chris Wright's message <https://www.redhat.com/en/blog/making-open-source-more-inclusive-eradicating-problematic-language>`_.

Welcome to the guide to building Ansible inventories.
An inventory is a list of managed nodes, or hosts, that Ansible deploys and configures.
This guide introduces you to inventories and covers the following topics:

* Creating inventories to track list of servers and devices that you want to automate.
* Using dynamic inventories to track cloud services with servers and devices that are constantly starting and stopping.
* Using patterns to automate specific sub-sets of an inventory.
* Expanding and refining the connection methods Ansible uses for your inventory.

.. toctree::
   :maxdepth: 2

   intro_inventory
   intro_dynamic_inventory
   intro_patterns
   connection_details