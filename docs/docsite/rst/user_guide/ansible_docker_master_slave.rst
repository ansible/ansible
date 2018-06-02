Getting Started
===============

What is this guide?
````````
This guide is about the pairing between Ansible, which is incredibily powerful, and Docker. Docker, which I will talk about later in great detail, is a great way to build and deploy your own custom image. Pairing these two together means that you can bring up and take down entire server infrastructures just with a few command line commands. We'll be using an Ansible-Playbook to setup and configure each of the servers exactly as we want them before getting the data. I recommend this practice to anyone interested in large scale web development and load testing.

Ansible
````````
Per Ansible, Ansible is a piece of software that automates software provisioning, configuration management (CM), and application deployment. Throughout this guide we'll use a few of those buzzwords like provision, CM, and deployment. In this particular case we'll use Ansible as a way to setup a server infrastructure without ever having to manually setup anything. Ansible will set everything up for us, we just need to give it a docker image to go from.

Docker
````````
Per Docker, docker is a computer program that performs operating-system-level virtualization known as containerization. That's really just a fancy way to saying container software.

Virtual Machines and VirtualBox
````````

Master: Ansible
````````

Slave: Docker
````````

Setting Up: Dockerfile and Image
````````

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

