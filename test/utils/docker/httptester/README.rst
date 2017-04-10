httptester
==========

HTTP Testing endpoint which provides httpbin, nginx, SSL and SNI
capabilities, for providing a local HTTP endpoint for testing

Building
--------

Docker
~~~~~~

Both ways of building docker utilize the ``nginx:alpine`` image, but can
be customized for ``Fedora``, ``Red Hat``, ``CentOS``, ``Ubuntu``,
``Debian`` and other variants of ``Alpine``

When utilizing ``packer`` or configuring with ``ansible-playbook``
the services will not automtically start on launch, and will have to be
manually started using::

    $ /services.sh

Such as when starting a docker container::

    docker run -ti --rm -p 80:80 -p 443:443 --name httptester ansible/ansible:httptester /services.sh

docker build
^^^^^^^^^^^^

::

    docker build -t ansible/ansible:httptester .

packer
^^^^^^

The packer build will use ``ansible-playbook`` to perform the
configuration, and will tag the image as ``ansible/ansible:httptester``

::

    packer build packer.json

Ansible
~~~~~~~

::

    ansible-playbook -i hosts -v httptester.yml

