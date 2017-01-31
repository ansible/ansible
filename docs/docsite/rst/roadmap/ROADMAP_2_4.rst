****************************
Ansible by Red Hat, Core 2.4
****************************
**********************
Target: June/July 2017
**********************

This is meant to be a living document, and is **DRAFT** until
stated otherwise in the document.

- **Python 2.4 and 2.5 support discontinuation**
  - Ansible will not support Python 2.4 nor 2.5 on the target hosts anymore. Going forward, Python 2.6+ will be required on targets, as already was the case for the controller.

- **Ansible-Config**
  - New yaml format for config
  - Extend the ability of the current config system by adding creating an ansible-config command and add the following:

    - Dump existing config settings

    - Update / write a config entry

    - Show available options (ini entry, yaml, env var, etc)

  - Proposal found in ansible/proposals issue `#35 <https://github.com/ansible/proposals/issues/35>`_.
  - Initial PR of code found in ansible/ansible PR `#12797 <https://github.com/ansible/ansible/pull/12797>`_.

- **Inventory Overhaul**

  - Current inventory is overtly complex, non modular and mostly still a legacy from inception. We also want to add a common set of features to most inventory sources but are hampered by the current code base.
  - Proposal found in ansible/proposals issue `#41 <https://github.com/ansible/proposals/issues/41>`_.

- **Facts Refreshening**

  - Make setup.py/facts more pluggable
  - Fact gathering policy finer grained
  - Improve testing of setup.py/facts.py

- **Cloud Provider Support**

  - Focus on pull requests for various modules
  - Triage existing merges

- **Contributor Quality of Life**

  - More bot improvements!
