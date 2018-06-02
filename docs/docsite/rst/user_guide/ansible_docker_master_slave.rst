Getting Started
===============

What is this guide?
````````
This guide is about the pairing between Ansible, which is incredibily powerful, and Docker. Docker, which I will talk about later in great detail, is a great way to build and deploy your own custom image. Pairing these two together means that you can bring up and take down entire server infrastructures just with a few command line commands. We'll be using an Ansible-Playbook to setup and configure each of the servers exactly as we want them before getting the data. I recommend this practice to anyone interested in large scale web development and load testing. For more information and details I can be contacted at bakermat@oregonstate.edu.

Ansible
````````
Per Ansible, Ansible is a piece of software that automates software provisioning, configuration management (CM), and application deployment. Throughout this guide we'll use a few of those buzzwords like provision, CM, and deployment. In this particular case we'll use Ansible as a way to setup a server infrastructure without ever having to manually setup anything. Ansible will set everything up for us, we just need to give it a docker image to go from.

Docker
````````
Per Docker, docker is a computer program that performs operating-system-level virtualization known as containerization. That's really just a fancy way to saying container software. The great thing about docker is its extensibility, with a relatively basic Dockerfile you can configure a static image based on just about anything. If you want Linux, you got it. If you want RedHat, you got it. If you want a basic linux image of about 5MB but you want SSH and only SSH, they've already got you covered. The DockerHub feature (which is also free) allows anyone to upload an image of their software for anyone else to download. For the purposes of this guide, I'll assume you've already got a DockerHub account.

Virtual Machines and VirtualBox
````````
For this guide, you'll need two virtual machines for one to represent the master and the other to represent the slave. I used a CentOS based VM running on VirtualBox. I won't be going into the details of how to setup a command line based CentOS distro because thats a separate guide in and of itself but suffice to say you'll need a linux based CLI for this guide. The key here is that you'll need two different boxes (virtualized or not) and the addresses I'll use to indicate that are 192.168.1.10 (Master) and 192.168.1.11 (Slave).

Slave: Docker
````````
On the slave, you'll need to install a few things in order to get started. Let's start with installing Docker
.. code-block:: bash
  $ sudo yum install -y yum-utils device-mapper-persistent-data lvm2
  $ sudo yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
  $ sudo yum install -y docker-ce
  $ sudo systemctl start docker
  $ sudo systemctl enable docker
  $ sudo usermod -aG docker user

Setting Up: Dockerfile and Image
````````


Master: Ansible
````````

Setting Up: New RSA Key

Setting Up: Ansible-Playbook
````````

Setting Up: Connecting Over SSH to each container
````````

Setting Up: Provisioning Each Container
````````

Testing: SSH
````````

Testing: Serving the Correct page
````````

Troubleshooting: Connecting to the right image
````````

Troubleshooting: Installing packages
````````

