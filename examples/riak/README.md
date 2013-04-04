#### Introduction

These example playbooks should help you get an idea of how to use the riak ansible module.  These playbooks were tested on Ubuntu Precise (12.04).

#### Hosts File Naming Conventions

In the hosts file, we define the different groups to ease the cluster joining process.

* **riakcluster_primary** - all nodes attempt to join this node. There should only be one member of this group.
* **riakcluster_last** - this node plans and commits changes to the cluster, in this example, the joining of the nodes.  
* **riakcluster_middle** - all nodes in between are members of this group.

 
There is no concept of node roles in Riak proper, it is master-less.

You can build an entire cluster by first modifying the hosts file to fit your
network.

#### Using the Playbooks

Here are the playbooks that you can use with the ansible-playbook commands:

* **deploy.yaml** - creates a complete riak cluster, it calls install.yaml and form_cluster.yaml
* **install.yaml** - tunes the operating system and installs Riak
* **form_cluster.yaml** - forms a riak cluster
* **rolling_restart.yaml** - demonstrates the ability to perform a rolling
configuration change.  Similar principals could apply to performing
rolling upgrades of Riak itself.

