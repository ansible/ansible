**********
httptester
**********

.. contents:: Topics

HTTP Testing endpoint which provides httpbin, nginx, SSL and SNI
capabilities, for providing a local HTTP endpoint for testing

Source files can be found at `test/utils/docker/httptester/ <https://github.com/ansible/ansible/tree/devel/test/utils/docker/httptester>`_

Building
========

Docker
------

Both ways of building docker utilize the ``nginx:alpine`` image, but can
be customized for ``Fedora``, ``Red Hat``, ``CentOS``, ``Ubuntu``,
``Debian`` and other variants of ``Alpine``

When utilizing ``packer`` or configuring with ``ansible-playbook``
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

The packer build will use ``ansible-playbook`` to perform the
configuration, and will tag the image as ``ansible/ansible:httptester``

::

    cd test/utils/docker/httptester
    packer build packer.json

Ansible
=======

::
    cd test/utils/docker/httptester
    ansible-playbook -i hosts -v httptester.yml

