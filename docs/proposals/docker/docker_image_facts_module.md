
# Docker_Image_Facts Module Proposal

## Purpose and Scope

The purpose of docker_image_facts is to inspect docker images.

Docker_image_facts will use docker-py to communicate with either a local or remote API. It will
support API versions >= 1.14. API connection details will be handled externally in a shared utility module similar
to how other cloud modules operate.

## Parameters

Docker_image_facts will support the parameters listed below. API connection parameters will be part of a shared
utility module as mentioned above.

```
name:
  description:
    - An image name or list of image names. The image name can include a tag using the format C(name:tag).
  default: null
```

## Examples

```
- name: Inspect all images
  docker_image_facts
  register: image_facts
  
- name: Inspect a single image
  docker_image_facts:
    name: myimage:v1
  register: myimage_v1_facts
```

## Returns

```
{
   changed: False
   failed: False
   rc: 0
   result: [ < inspection output > ]
}
```

