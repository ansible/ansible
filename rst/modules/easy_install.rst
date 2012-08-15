.. _easy_install:

easy_install
````````````

.. versionadded:: 0.7

The easy_install module installs Python libraries. 

+--------------------+----------+---------+----------------------------------------------------------------------------+
| parameter          | required | default | comments                                                                   |
+====================+==========+=========+============================================================================+
| name               | yes      |         | a Python library name                                                      |
+--------------------+----------+---------+----------------------------------------------------------------------------+
| virtualenv         | no       |         | an optional virtualenv directory path to install into, if the virtualenv   |
|                    |          |         | does not exist it is created automatically                                 |
+--------------------+----------+---------+----------------------------------------------------------------------------+

Please note that the easy_install command can only install Python libraries. 
Thus this module is not able to remove libraries. It is generally recommended to 
use the :ref:`pip` module which you can first install using easy_install. 

Also note that `virtualenv <http://www.virtualenv.org/>`_ must be installed on 
the remote host if the `virtualenv` parameter is specified.

Example action from Ansible :doc:`playbooks`::

    easy_install name=pip
    easy_install name=flask==0.8
    easy_install name=flask virtualenv=/srv/webapps/my_app/venv
