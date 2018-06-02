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

Let's setup the ``hosts.ini`` which contains hosts (IP addresses) and their associated variables. Open the ``hosts.ini`` file with ``vi hosts.ini`` and add the following:

.. code-block:: txt

  [slave]
  192.168.1.11
  
  [slave:vars]
  ansible_connection=ssh
  ansible_port=22
  ansible_user=root
  ansible_python_interpreter=/usr/bin/python3
  
  [slaves]
  192.168.1.101
  192.168.1.102
  
  [slaves:vars]
  ansible_connection=ssh
  ansible_port=50222
  ansible_user=root
  ansible_python_interpreter=/usr/bin/python3
  
To briefly explain; the ``[slave]`` block is the IP of the Slave box we setup earlier and the ``[vars]`` block concerns how ansible will connect and make changes. As usual, we have't changed much from the basic ansible setup: connect over SSH to root and use the python3 interpreter is all this says.
  

Master: Startup.yaml Playbook
````````
Let's get more complicated! The ansible playbook is a file thats built in the Yet Another Markup Language (YAML) format. Its a bit wierd but it works and that's all we care about. Remember that ``.yaml`` file we used ``touch`` on earlier? Let's open that up with ``vi startup.yaml``. Recall: ansible uses spacing as a way to delinate meaning, so don't mess up the spacing.

.. code-block:: txt

  ---
  - hosts: slave
    gather_facts: no
    become: true
    tasks:
    - name: Start server 1
      raw: ip addr add 192.168.1.101 dev enp0s3 && docker run -d --rm --name server1 -p 192.168.1.101:8080:8080 -p 192.168.1.101:50222:22 user/server_node:1.0
    - name: Start server 2
      raw: ip addr add 192.168.1.102 dev enp0s3 && docker run -d --rm --name server2 -p 192.168.1.102:8080:8080 -p 192.168.1.102:50222:22 user/server_node:1.0
      
  - hosts: slaves
    gather_facts: no
    become: true
    tasks:
    - name: Add index into place on the slave
      template:
        src: ansible-index.html
        dest: /srv/ansible-index.html
    - name: Install the forever tool
      raw: npm install -g forever
    - name: Run the slave server
      forever start /srv/server.js

I know that was quite a lot to add to your ansible playbook but lets take a moment and briefly walk through it. In the ``hosts`` section that specifies which hosts we are talking about (again from the hosts.ini file from earlier). So we start with the Slave node (which has nothing running on it) and we choose not to ``gather_facts``. Gather_facts gathers data about the host but the issue with it is that it might fail due to a lack of python. So we skip it for now. Next up is ``become``, which we need because ``become`` indicates to ansible that it should ``become`` root. The ``tasks`` block concerns everything that ansible will have to take care of for that set of hosts (in this case just the Slave). There are two listed tasks and ansible will run both of them directly on the Slave. The first adds an IP address interface and then runs the first docker server and then second does the same but with a different IP address. 


On the next set of hosts the commands are quite a bit different. The hosts, indicated by ``slaves`` are the hosts of the nodes running on the Slaves each at ``192.168.1.101`` and ``192.168.1.102`` respectively. Just like the main Slave, we choose to not gather facts about the hosts and we choose to become root. Next we ``template`` our index into place (which I'll detail what to put in there later) and then we install the ``npm`` tool known as ``forever``. The ``forever`` tool allows things like nodejs to run in the background forever, which is exactly what we need. And finally, we run the server.js file we made earlier using the ``forever`` tool.

Master: Ansible-index.html
````````
Let's next create the ``ansible-index.html`` file which as we just saw in the ansible playbook we will ``template`` using the ``template`` source and destination function. Let's open it up using ``vi ansible-index.html`` and add the following:

.. code-block:: html

  <html>
  <head><title>Slave Docker Server</title></head>
  <body>
  <p>Templated page from Ansible</p>
  <p>Last provisioned on {{ template_run_date }}</p>
  </body>
  </html>
  
This is a very basic html page that will be served up by our nodejs server after being templated by ansible. You can add whatever you might like to make it a little more exciting but the only thing we're going to do is just ``template`` it later on and ``curl`` it.

Master: Startup Script
````````
Next, lets open up that startup bash script and add a few important things to make it easier on ourselves later on. Open it with ``vi startup.S`` and add the following:

.. code-block:: txt

  #!/bin/bash
  clear
  export ANSIBLE_HOST_KEY_CHECKING=false
  ssh-keyscan 192.168.1.11 >> ~/.ssh/known_hosts
  ansible-playbook startup.yaml -i hosts.ini
  
Let's walk through exactly what this script is doing. The first thing this script does is clear the terminal, for ease and cleanliness (always a nice thing). Next up it exports a certain variable, and this is what the ansible documentation says about it:

.. code-block:: txt

  If a host is reinstalled and has a different key in ‘known_hosts’, this will result in an error message until corrected. If a host is not initially in ‘known_hosts’ this will result in prompting for confirmation of the key, which results in an interactive experience if using Ansible, from say, cron. You might not want this.
  
The keyscan is just for the main Slave which is not always checked by the first export we just added. Just for being double-sure. That last command runs the ansible playbook we just made using the ``hosts.ini`` file specifying the Slave and Slaves. The last thing you need to do is chmod it; ``chmod +x startup.S``.

Let's run it!! ``./startup.S``. You'll see a bunch of text as ansible works through each of the Slaves and their associated tasks. Installing forever on each of the containers can take a little while so sit back, relax and just wait. Total processing time should be about 2 - 3 minutes. Not too shabby.

Master: Curl Each Server
````````
On the master this is the last task that we'll use as a way to see if everything worked correctly. Run the following on the command line on the master and if we're lucky you'll get back a basic html page (the one we made earlier) with a provisioned time that is different for each IP address ``192.168.1.101`` and ``192.168.1.102``.

.. code-block:: bash

  $ curl 192.168.1.101:8080
  $ curl 192.168.1.102:8080
  
If not, that means something went wrong and you should check over to make sure that all of the steps previously were followed and if you think that they were please refer to the following sections for more troubleshooting and debugging help. Otherwise, good job!

Troubleshooting: Connecting Over SSH to each container
````````

Troubleshooting: Provisioning Each Container
````````

Troubleshooting: Serving the Correct page
````````

Troubleshooting: Installing packages
````````

