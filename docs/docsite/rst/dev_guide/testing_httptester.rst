**********
httptester
**********

.. contents:: Topics

Overview
========

``httptester`` is a docker container used to host certain resources required by :doc:`testing_integration`. This is to avoid CI tests requiring external resources (such as git or package repos) which, if temporarily unavailable, would cause tests to fail.

HTTP Testing endpoint which provides the following capabilities:

* httpbin
* nginx
* SSL
* SNI


Source files can be found at `test/utils/docker/httptester/ <https://github.com/ansible/ansible/tree/devel/test/utils/docker/httptester>`_

Building
========

Docker
------

Both ways of building ``docker`` utilize the ``nginx:alpine`` image, but can
be customized for ``Fedora``, ``Red Hat``, ``CentOS``, ``Ubuntu``,
``Debian`` and other variants of ``Alpine``

When utilizing ``packer`` or configuring with ``ansible-playbook``,
the services will not automatically start on launch, and will have to be
manually started using::

    cd test/utils/docker/httptester
    ./services.sh

Such as when starting a docker container::

    cd test/utils/docker/httptester
    docker run -ti --rm -p 80:80 -p 443:443 --name httptester ansible/ansible:httptester /services.sh

docker build
------------

::

    cd test/utils/docker/httptester
    docker build -t ansible/ansible:httptester .

packer
------

The ``packer`` build will use ``ansible-playbook`` to perform the
configuration, and will tag the image as ``ansible/ansible:httptester``::

    cd test/utils/docker/httptester
    packer build packer.json

Ansible
=======

::
    cd test/utils/docker/httptester
    ansible-playbook -i hosts -v httptester.yml


Extending httptester
====================

If you have sometime to improve ``httptester`` please add a comment on the `Testing Working Group Agenda <https://github.com/ansible/community/blob/master/meetings/README.md>`_ to avoid duplicated effort.
