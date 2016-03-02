
# Docker_Volume_Facts Module Proposal

## Purpose and Scope

Docker_volume_facts will inspect volumes.

Docker_volume_facts will use docker-py to communicate with either a local or remote API. It will
support API versions >= 1.14. API connection details will be handled externally in a shared utility module similar
to how other cloud modules operate.

## Parameters

Docker_volume_facts will accept the parameters listed below. API connection parameters will be part of a shared
utility module as mentioned above.


```
name:
  description:
    - Volume name or list of volume names. 
  default: null
```


## Examples

```
- name: Inspect all volumes
  docker_volume_facts
  register: volume_facts
  
- name: Inspect a specific volume
  docker_volume_facts:
    name: data
  register: data_vol_facts
```

# Returns

```
{
   changed: False
   failed: False
   rc: 0
   results: [ < output from volume inspection  > ]
}
```