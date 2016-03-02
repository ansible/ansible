
# Docker_Network_Facts Module Proposal

## Purpose and Scope

Docker_network_facts will inspect networks.

Docker_network_facts will use docker-py to communicate with either a local or remote API. It will
support API versions >= 1.14. API connection details will be handled externally in a shared utility module similar
to how other cloud modules operate.

## Parameters

Docker_network_facts will accept the parameters listed below. API connection parameters will be part of a shared
utility module as mentioned above.

```
name:
  description:
    - Network name or list of network names. 
  default: null

```


## Examples

```
- name: Inspect all networks
  docker_network_facts
  register: network_facts

- name: Inspect a specific network and format the output
  docker_network_facts
    name: web_app
  register: web_app_facts
```

# Returns

```
{
   changed: False
   failed: False
   rc: 0
   results: [ < inspection output > ]
}
```
