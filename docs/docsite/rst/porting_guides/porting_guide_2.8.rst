.. _porting_2.8_guide:

*************************
Ansible 2.8 Porting Guide
*************************

This section discusses the behavioral changes between Ansible 2.7 and Ansible 2.8.

It is intended to assist in updating your playbooks, plugins and other parts of your Ansible infrastructure so they will work with this version of Ansible.

We suggest you read this page along with `Ansible Changelog for 2.8 <https://github.com/ansible/ansible/blob/devel/changelogs/CHANGELOG-v2.8.rst>`_ to understand what updates you may need to make.

This document is part of a collection on porting. The complete list of porting guides can be found at :ref:`porting guides <porting_guides>`.

.. contents:: Topics

Playbook
========

No notable changes.


Command Line
============

Become Prompting
----------------

Beginning in version 2.8, by default Ansible will use the word ``BECOME`` to prompt you for a password for elevated privileges (``sudo`` privileges on unix systems or ``enable`` mode on network devices):

By default in Ansible 2.8::

    ansible-playbook --become --ask-become-pass site.yml
    BECOME password:

If you want the prompt to display the specific ``become_method`` you're using, instead of the agnostic value ``BECOME``, set :ref:`AGNOSTIC_BECOME_PROMPT` to ``False`` in your Ansible configuration.

By default in Ansible 2.7, or with ``AGNOSTIC_BECOME_PROMPT=False`` in Ansible 2.8::

    ansible-playbook --become --ask-become-pass site.yml
    SUDO password:

Deprecated
==========

* Setting the async directory using ``ANSIBLE_ASYNC_DIR`` as an task/play environment key is deprecated and will be
  removed in Ansible 2.12. You can achieve the same result by setting ``ansible_async_dir`` as a variable like::

      - name: run task with custom async directory
        command: sleep 5
        async: 10
        vars:
          ansible_aync_dir: /tmp/.ansible_async


Modules
=======

Major changes in popular modules are detailed here

The exec wrapper that runs PowerShell modules has been changed to set ``$ErrorActionPreference = "Stop"`` globally.
This may mean that custom modules can fail if they implicitly relied on this behaviour. To get the old behaviour back,
add ``$ErrorActionPreference = "Continue"`` to the top of the module. This change was made to restore the old behaviour
of the EAP that was accidentally removed in a previous release and ensure that modules are more resiliant to errors
that may occur in execution.


Modules removed
---------------

The following modules no longer exist:

* ec2_remote_facts
* azure
* cs_nic
* netscaler
* win_msi

Deprecation notices
-------------------

The following modules will be removed in Ansible 2.12. Please update your playbooks accordingly.

* ``foreman`` use <https://github.com/theforeman/foreman-ansible-modules> instead.
* ``katello`` use <https://github.com/theforeman/foreman-ansible-modules> instead.


Noteworthy module changes
-------------------------

* The ``foreman`` and ``katello`` modules have been deprecated in favor of a set of modules that are broken out per entity with better idempotency in mind.
* The ``foreman`` and ``katello`` modules replacement is officially part of the Foreman Community and supported there.
* The ``tower_credential`` module originally required the ``ssh_key_data`` to be the path to a ssh_key_file.
  In order to work like Tower/AWX, ``ssh_key_data`` now contains the content of the file.
  The previous behavior can be achieved with ``lookup('file', '/path/to/file')``.
* The ``win_scheduled_task`` module deprecated support for specifying a trigger repetition as a list and this format
  will be removed in Ansible 2.12. Instead specify the repetition as a dictionary value.

* The ``win_feature`` module has removed the deprecated ``restart_needed`` return value, use the standardised
  ``reboot_required`` value instead.

* The ``win_package`` module has removed the deprecated ``restart_required`` and ``exit_code`` return value, use the
  standardised ``reboot_required`` and ``rc`` value instead.

* The ``win_get_url`` module has removed the deprecated ``win_get_url`` return dictionary, contained values are
  returned directly.

* The ``win_get_url`` module has removed the deprecated ``skip_certificate_validation`` option, use the standardised
  ``validate_certs`` option instead.


Plugins
=======

* The ``powershell`` shell plugin now uses ``async_dir`` to define the async path for the results file and the default
  has changed to ``%USERPROFILE%\.ansible_async``. To control this path now, either set the ``ansible_async_dir``
  variable or the ``async_dir`` value in the ``powershell`` section of the config ini.

Porting custom scripts
======================

No notable changes.

Networking
==========

No notable changes.
