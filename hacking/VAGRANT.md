Vagrant Setup
=============

Prerequisites
-------------

1. [Vagrant 1.1+](http://www.vagrantup.com/)
2. [VirtualBox](https://www.virtualbox.org/) or some other VM provider
[supported by Vagrant](http://docs.vagrantup.com/v2/providers/index.html)


Setup
-----

1. Run `vagrant up`. That command will:
    1. Download a VM image of Ubuntu 12.04
    2. Create a VM instance based on that image
    3. Provision it with necessary packages
2. Run `vagrant ssh`. That command will SSH you inside a VM.
3. Once inside a VM, go to `/opt/ansible` and run some tests:

    ```bash
    cd /opt/ansible
    make tests
    ```

4. You're good to go!
