# Docker_Network Module Proposal

## Purpose and Scope:

The purpose of Docker_network is to create networks, connect containers to networks, disconnect containers from 
networks, and delete networks.

Docker network will manage networks using docker-py to communicate with either a local or remote API. It will
support API versions >= 1.14. API connection details will be handled externally in a shared utility module similar to
how other cloud modules operate.

## Parameters:

Docker_network will accept the parameters listed below. Parameters related to connecting to the API will be handled in 
a shared utility module, as mentioned above.

```
connected:
  description:
    - List of container names or container IDs to connect to a network.
  default: null

driver:
  description:
    - Specify the type of network. Docker provides bridge and overlay drivers, but 3rd party drivers can also be used.
  default: bridge

driver_options:
  description:
    - Dictionary of network settings. Consult docker docs for valid options and values.
  default: null

force:
  description:
    - With state 'absent' forces disconnecting all containers from the network prior to deleting the network. With
      state 'present' will disconnect all containers, delete the network and re-create the network.
  default: false

incremental:
  description:
    - By default the connected list is canonical, meaning containers not on the list are removed from the network.
      Use incremental to leave existing containers connected.
  default: false

ipam_driver:
  description:
    - Specifiy an IPAM driver.
  default: null 

ipam_options:
  description:
    - Dictionary of IPAM options.  
  default: null

network_name:
  description:
    - Name of the network to operate on.
  default: null
  required: true
    
state:
  description:
    - "absent" deletes the network. If a network has connected containers, it cannot be deleted. Use the force option
      to disconnect all containers and delete the network.
    - "present" creates the network, if it does not already exist with the specified parameters, and connects the list
      of containers provided via the connected parameter. Containers not on the list will be disconnected. An empty
      list will leave no containers connected to the network. Use the incremental option to leave existing containers
      connected. Use the force options to force re-creation of the network.
  default: present
  choices:
    - absent
    - present
```


## Examples:

```
- name: Create a network
  docker_network:
    name: network_one

- name: Remove all but selected list of containers
  docker_network:
    name: network_one
    connected:
      - containera
      - containerb
      - containerc

- name: Remove a single container
  docker_network:
    name: network_one
    connected: "{{ fulllist|difference(['containera']) }}"
       
- name: Add a container to a network, leaving existing containers connected
  docker_network:
    name: network_one
    connected:
      - containerc
    incremental: yes
   
- name: Create a network with options (Not sure if 'ip_range' is correct key name)
  docker_network
    name: network_two
    options:
      subnet: '172.3.26.0/16'
      gateway: 172.3.26.1
      ip_range: '192.168.1.0/24'

- name: Delete a network, disconnecting all containers
  docker_network:
    name: network_one
    state: absent
    force: yes      
```

## Returns:

```
{
    changed: True,
    failed: false
    rc: 0
    action: created | removed | none
    results: {
        < results from docker inspect for the affected network >
    }
}
```
