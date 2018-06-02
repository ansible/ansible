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
On the slave, you'll need to install a few things in order to get started. Let's start with installing Docker:

.. code-block:: bash

  $ sudo yum install -y yum-utils device-mapper-persistent-data lvm2
  $ sudo yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
  $ sudo yum install -y docker-ce
  $ sudo systemctl start docker
  $ sudo systemctl enable docker
  $ sudo usermod -aG docker user

Master: Generate RSA Key
````````
Next, hop on over to the Master and generate that RSA key! We'll need to use this so that Ansible can SSH without the need for a password onto each of the containers for provisioning and the slave for the initial setup. This must be done correctly, so make sure that everything is configured properly.

.. code-block:: bash

  $ ssh-keygen -t rsa
  
Hit enter three times to set no password and to accept the storage location that is set by default. Then check the location ``~/.ssh/id_rsa.pub`` and make sure that the file exists and contains an RSA key. If it does not, head back to the previous code block and make sure that you followed the command correctly. This is very important.

Next, copy that key from the Master over to the Slave. We'll need to bake it in directly to the dockerfile so that Ansible doesn't have any SSH authentication issues.

.. code-block:: bash

  $ scp ~/.ssh/id_rsa.pub root@192.168.1.11:/root/.ssh/authorized_keys
  enter password
  $ scp ~/.ssh/id_rsa.pub root@192.168.1.11:/home/user/id_rsa.pub
  enter password
  
  $ ssh root@192.168.1.11
  no password should be needed
  
Slave: Baking The Dockerfile and Server.js into the Image
````````
Head back on over to the slave and lets check that everything copied correctly and worked out just right. Check that your public key is present in ``/root/.ssh/authorized_keys`` and that a copy of the public key also exists at ``/home/user/id_rsa.pub``. If not, go back to the previous step and attempt to copy it again.

Let's move on to building the Dockerfile next. In a previous guide I went over some of the basics of this so we'll move through it pretty quickly. Create a file called ``Dockerfile`` at the directory level of ``/home/user/``. 

.. code-block:: txt

  # Dockerfile for servers of the Slave
  FROM gotechnies/alpine-ssh:latest
  MAINTAINER YourName <yourEmail@email.com>
  
  RUN apk -U add nodejs
  RUN apk -U add python3
  
  # Copy the right files over to the image
  COPY server.js /srv/server.js
  COPY id_rsa.pub /root/.ssh/authorized_keys
  
  # Expose 8080 and 22 for HTTP and SSH, respectively
  EXPOSE 8080
  EXPOSE 22
  
Next up, lets write a similar node server to what I did previously. No sense in remaking the wheel. Call this file ``server.js`` for simplicity's sake.

.. code-block:: txt

  var fs = require('fs');
  var ansi = fs.readFileSync("/srv/ansible-index.html");
  var http = require('http');
  
  http.createServer(function (request, response)
  {
    response.writeHead(200, {'Content-Type': 'text/plain'});
    response.end(ansi);
  }).listen(8080);

Write and quit both of those and make sure they are saved in the same directory, ``/home/user/``. Let's build the image and push it to the DockerHub server so that other people (and us later on) can use our image. Replace the instance of ``user`` with your DockerHub username.

.. code-block:: bash

  $ docker build -t user/server_node:1.0 .
  $ docker push user/server_node:1.0
  
If you are not logged in on the command line there are lots of tutorials for logging in on the CLI so hop over to google and use the first one you find. I mentioned the guide previously in my last guide.

Let's make sure that everything is cleaned up on the Slave with the following

.. code-block:: bash

  $ docker kill $(docker ps -q)
  $ docker system prune -a
  
That will take down any processes you might have and delete any built images on your system. Do that every once in a while to make sure your space isn't being taken up needlessly. You should see about 90 - 110 MB freed. 

On a quick side note, if you find yourself tired of typing those commands out and you want to make things quicker. Whip up the following ``takeDown.S`` script:

.. code-block:: txt

  sudo ip addr del 192.168.1.101/32 dev enp0s3
  sudo ip addr del 192.168.1.102/32 dev enp0s3
  docker kill $(docker ps -q)
  docker system prune -a
  
Save that file then make sure its executable with ``chmod +x takeDown.S``. Then you can execute it with ``./takeDown.S`` and that will take care of everything on your current system so you can connect and start again with ansible without much of an issue. We'll get to the details of why you need those first two later on but you can keep them in the script for now.

Master: Ansible
````````
Swap on over to the Master, located at the previously explained 192.168.1.10 (or whatever your Master's IP is). First we need to install ansible, which we'll use to monitor and provision the Slave. Install it with the following:

.. code-block:: bash

  $ sudo yum install -y ansible
  
Next, let's move on to the files we'll need.

Master: Creating the files you'll need
````````
Touch each of the following to create them. ``hosts.ini`` will contain the hosts both for the Slave and the nodes of the Slave. ``startup.yaml`` is the ansible playbook which we'll use to provision the nodes. ``ansible-index.html`` is the provisioned file, which we'll use to update the timestamp. ``id_rsa.pub`` is the public rsa key of the Master. ``startup.S`` is the script we'll use to run the ansible playbook and set the keyscan parameters. And at the end we'll ``curl`` each of the servers to get the provisioned page.

.. code-block:: bash

  $ touch hosts.ini
  $ touch startup.yaml
  $ touch ansible-index.html
  $ touch startup.S
  $ chmod +x startup.S
  $ touch curl.S
  $ chmod +x curl.S
  
That should cover all of the scripts we need to create. From the copy action we did earlier, we should already have the public rsa key we need for password-less SSH'ing.

Master: Hosts.ini
````````

Master: Startup.yaml Playbook
````````

Master: Ansible-index.html
````````

Master: Id_rsa.pub
````````

Master: Startup Script
````````

Master: Curl Each Server
````````


Troubleshooting: Connecting Over SSH to each container
````````

Troubleshooting: Provisioning Each Container
````````

Troubleshooting: Serving the Correct page
````````

Troubleshooting: Installing packages
````````

