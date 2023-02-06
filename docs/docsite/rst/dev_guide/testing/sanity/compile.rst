.. _testing_compile:

compile
=======

All Python source files must successfully compile using all supported Python versions.

.. note::

   The list of supported Python versions is dependent on the version of ``ansible-core`` that you are using.
   Make sure you consult the version of the documentation which matches your ``ansible-core`` version.

Controller code, including plugins in Ansible Collections, must support the following Python versions:

- 3.11
- 3.10
- 3.9

Code which runs on targets (``modules`` and ``module_utils``) must support all controller supported Python versions,
as well as the additional Python versions supported only on targets:

- 3.8
- 3.7
- 3.6
- 3.5
- 2.7

.. note::

   Ansible Collections can be
   `configured <https://github.com/ansible/ansible/blob/devel/test/lib/ansible_test/config/config.yml>`_
   to support a subset of the target-only Python versions.
