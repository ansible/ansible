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
containers:

network_name:
  description:
    - Name of the network to operate on.
  default: null
  required: true

driver:
  description:
    - Specify the type of network. Docker provides bridge and overlay drivers, but 3rd party drivers can also be used.
  default: bridge

options:
  description:
    - Dictionary of network settings. Consult docker docs for valid options and values.
  default: null

connected:
  description:
    - List of container names or container IDs to connect to a network.
  default: null
  
disconnected:
  description:
    - List of container names or container IDs to disconnect from a network.
  default: null

disconnect_all:
  description:
    - Disconnect all containers, unless the containers is in the provided list of connected containers. If no
      list of connected containers is provided, all containers will be disconnnected.
  default: false

force:
  description:
    - With state 'absent' forces disconnecting all containers from the network prior to deleting the network. With
      state 'present' will disconnect all containers, delete the network and re-create the network.
    default: false
    
state:
  description:
    - "absent" deletes the network. If a network has connected containers, it cannot be deleted. Use the force option
      to disconnect all containers and delete the network.
    - "present" creates the network, if it does not already exist with the specified parameters, and connects the list
      of containers provided via the connected parameter. Use disconnected to remove a set of containers from the
      network. Use disconnect_all to remove from the network any containers not included in the containers parameter.
      If disconnected is provided with no list of connected parameter, all containers will be removed from the 
      network. Use the force options to force the re-creation of the network.
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
    disconnect_all: yes

- name: Remove a container from the network
  docker_network:
    name: network_one
    disconnected:
      - containerb

- name: Delete a network, disconnected all containers
  docker_network:
    name: network_one
    state: absent
    force: yes
    
- name: Add a container to a network
  docker_network:
    name: network_one
    connected:
      - containerc
      
- name: Create a network with options (Not sure if 'ip_range' is correct name)
  docker_network
    name: network_two
    options:
      subnet: '172.3.26.0/16'
      gateway: 172.3.26.1
      ip_range: '192.168.1.0/24'
      
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