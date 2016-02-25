
# Docker_Image_Facts Module Proposal

## Purpose and Scope

The purpose of docker_image_facts is to provide similar functionality to `docker images` and `docker history`.

Docker_image_facts will use docker-py to communicate with either a local or remote API. It will
support API versions >= 1.14. API connection details will be handled externally in a shared utility module similar
to how other cloud modules operate.

## Parameters

Docker_image_facts will support the parameters listed below. API connection parameters will be part of a shared
utility module as mentioned above.

```
all:
  description:
    - When listing images, show all images, including intermediate.
  default: false

digests:
  description:
    - When listing images, show digests.
  default: false

filters:
  description:
    - When listing images, provide filters in the format "key=value".
  default: null

human:
  description:
    - When getting image history, print sizes and dates in human readable form.
  default: true

mode:
  description:
    - List available images or show the history of an image.
  default: list
  choices:
    - list
    - history

name:
  description:
    - Image name or repository. Required when mode is 'history'
  default: null

quiet:
  description:
    - Only show numeric IDs.
  default: false

tag:
  description:
    - Use in conjunction with name to filter results
  default: null

truncate:
  description:
    - Truncate output.
  default: false
```

## Returns

```
{
   changed: False
   failed: False
   results: [
      < history or list of matching images >
   ]
}
```

## Examples

```
- name: list images
  docker_image_facts:
    mode: list
    filters:
      - "foo=bar"

- name: list images for specific name and tag
  docker_image_facts:
    mode: list
    name: myimage
    tag: foo

- name: show image history
  docker_image_facts:
    mode: history
    name: myimage
    tag: foo
```
