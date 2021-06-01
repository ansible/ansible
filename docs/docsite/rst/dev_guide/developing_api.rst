.. _developing_api:

**********
Python API
**********

.. contents:: Topics

.. note:: This API is intended for internal Ansible use. Ansible may make changes to this API at any time that could break backward compatibility with older versions of the API. Because of this, external use is not supported by Ansible. If you want to use Python API only for executing playbooks or modules, consider `ansible-runner <https://ansible-runner.readthedocs.io/en/latest/>`_ first.

There are several ways to use Ansible from an API perspective.   You can use
the Ansible Python API to control nodes, you can extend Ansible to respond to various Python events, you can
write plugins, and you can plug in inventory data from external data sources.  This document
gives a basic overview and examples of the Ansible execution and playbook API.

If you would like to use Ansible programmatically from a language other than Python, trigger events asynchronously,
or have access control and logging demands, please see the `AWX project <https://github.com/ansible/awx/>`_.

.. note:: Because Ansible relies on forking processes, this API is not thread safe.

.. _python_api_example:

Python API example
==================

This example is a simple demonstration that shows how to minimally run a couple of tasks:

.. literalinclude:: ../../../../examples/scripts/uptime.py
   :language: python

.. note:: Ansible emits warnings and errors via the display object, which prints directly to stdout, stderr and the Ansible log.

The source code for the ``ansible``
command line tools (``lib/ansible/cli/``) is `available on GitHub <https://github.com/ansible/ansible/tree/devel/lib/ansible/cli>`_.

.. seealso::

   :ref:`developing_inventory`
       Developing dynamic inventory integrations
   :ref:`developing_modules_general`
       Getting started on developing a module
   :ref:`developing_plugins`
       How to develop plugins
   `Development Mailing List <https://groups.google.com/group/ansible-devel>`_
       Mailing list for development topics
   `irc.libera.chat <https://libera.chat>`_
       #ansible IRC chat channel
