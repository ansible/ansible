
# Docker_Image Module Proposal

## Purpose and Scope

The purpose is to update the existing docker_image module. The updates include expanding the module's capabilities to
match the build, load, pull, push, rmi, and save docker commands and adding support for remote registries.

Docker_image will manage images using docker-py to communicate with either a local or remote API. It will
support API versions >= 1.14. API connection details will be handled externally in a shared utility module similar 
to how other cloud modules operate.

## Parameters

Docker_image will support the parameters listed below. API connection parameters will be part of a shared utility 
module as mentioned above.

```
archive_path:
  description:
    - Save image to the provided path. Use with state present to always save the image to a tar archive. If
      intermediate directories in the path do not exist, they will be created. If a matching
      archive already exists, it will be overwritten.
  default: null

config_path:
  description:
    - Path to a custom docker config file. Docker-py defaults to using ~/.docker/config.json.

cgroup_parent:
  description:
    - Optional parent cgroup for build containers.
  default: null

cpu_shares:
  description:
    - CPU shares for build containers. Integer value.
  default: 0

cpuset_cpus:
  description:
    - CPUs in which to allow build container execution C(1,3) or C(1-3).
  default: null

dockerfile:
  description:
    - Name of dockerfile to use when building an image.
  default: Dockerfile

email:
  description:
    - The email for the registry account. Provide with username and password when credentials are not encoded
      in docker configuration file or when encoded credentials should be updated.
  default: null
  nolog: true

force:
  description:
    - Use with absent state to un-tag and remove all images matching the specified name. Use with present state to
      force a pull or rebuild of the image.
  default: false

load_path:
  description:
    - Use with state present to load a previously save image. Provide the full path to the image archive file.
  default: null
  
memory:
  description:
    - Build container limit. Memory limit specified as a positive integer for number of bytes.

memswap:
  description:
    - Build container limit. Total memory (memory + swap). Specify as a positive integer for number of bytes or
      -1 to disable swap.
  default: null

name:
  description:
    - Image name or ID.
  required: true

nocache:
  description:
    - Do not use cache when building an image.
  deafult: false

password:
  description:
    - Password used when connecting to the registry. Provide with username and email when credentials are not encoded
      in docker configuration file or when encoded credentials should be updated.
  default: null
  nolog: true

path:
  description:
    - Path to Dockerfile and context from which to build an image.
  default: null

push:
  description:
    - Use with state present to always push an image to the registry.
  default: false

registry:
  description:
    - URL of the registry. If not provided, defaults to Docker Hub.
  default: null
  
rm:
  description:
    - Remove intermediate containers after build.
  default: true

tag:
  description:
    - Image tags. When pulling or pushing, set to 'all' to include all tags.
  default: latest

url:
  description:
    - The location of a Git repository. The repository acts as the context when building an image.
    - Mutually exclusive with path.

username:
  description:
    - Username used when connecting to the registry. Provide with password and email when credentials are not encoded 
      in docker configuration file or when encoded credentials should be updated.
  default: null
  nolog: true

state:
  description:
    - "absent" - if image exists, unconditionally remove it. Use the force option to un-tag and remove all images
      matching the provided name.
    - "present" - check if image is present with the provided tag. If the image is not present or the force option
      is used, the image will either be pulled from the registry, built or loaded from an archive. To build the image,
      provide a path or url to the context and Dockerfile. To load an image, use load_path to provide a path to
      an archive file. If no path, url or load_path is provided, the image will be pulled. Use the registry
      parameters to control the registry from which the image is pulled.
    
required: false
default: present
choices:
  - absent
  - present
  
http_timeout:
  description:
    - Timeout for HTTP requests during the image build operation. Provide a positive integer value for the number of
      seconds.
  default: null
  
```


## Examples

```
- name: build image
  docker_image:
    path: "/path/to/build/dir"
    name: "my_app"
    tags:
      - v1.0
      - mybuild

- name: force pull an image and all tags
  docker_image:
    name: "my/app"
    force: yes
    tags: all

- name: untag and remove image
  docker_image:
    name: "my/app"
    state: absent
    force: yes

- name: push an image to Docker Hub with all tags
  docker_image:
    name: my_image
    push: yes
    tags: all

- name: pull image from a private registry
  docker_image:
    name: centos
    registry: https://private_registry:8080

```


## Returns

```
{
   changed: True
   failed: False
   rc: 0
   action: built | pulled | loaded | removed | none
   msg: < text confirming the action that was taken >
   results: {
      < output from docker inspect for the affected image >
   }
}
```