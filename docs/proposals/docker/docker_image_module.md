
# Docker_Image Module Proposal

## Purpose and Scope

The purpose is to update the existing docker_images module so that it supports absent, built, present, pushed and
saved states and supports both local and remote API access.

Docker_image will manage images using docker-py to communicate with either a local or remote API. It will
support API versions >= 1.14. API connection details and registry authentication will be handled externally in a
shared utility module similar to how other cloud modules operate.

## Parameters

Docker_image will support the parameters listed below. API connection parameters will be part of a shared utility module
as mentioned above.

```
archive_path:
  description:
    - File name for the archive when saving an image.
  default: null

build_args:
  description:
    - List of build-time variables.
  default: null

cgroup_parent:
  description:
    - Optional parent cgroup for build containers.
  default: null

cpu_period:
  description:
    - Limit build container CPU CFS (Completely Fair Scheduler) period. Expressed in milliseconds.
  default: 0

cpu_quota:
  description:
    - Limit build container CPU CFS (Completely Fair Scheduler) quota. Expressed in milliseconds.
  default: 0

cpu_shares:
  description:
    - CPU shares for build containers. Integer value.
  default: 0

cpuset_cpus:
  description:
    - CPUs in which to allow build container execution C(1,3) or C(1-3).
  default: null

cpuset_mems:
  description:
    - Memory nodes (MEMs) in which to allow build container execution. For example, C(0-3) or C(0,1).
  default: null

dockerfile:
  description:
    - Name of dockerfile to use when building an image.
  default: Dockerfile

force:
  description:
    - Use with absent state to untag and remove all images matching the specified name. Use with built state to
      force rebuilding of an image.
  default: false

name:
  description:
    - Image name or Image ID.
  required: true

nocache:
  description:
    - Do not use cache when building
  deafult: false

path:
  description:
    - Path to Dockerfile and context from which to build an image.
  default: null

registry:
  description:
    - host or host:port of a remote registry.
  required: false

rm:
  description:
    - Remove itermediate containers after build.
  default: true

shm_size:
  description:
    - For build containers. Size of `/dev/shm`. The format is `<number><unit>`. `number` must be greater than `0`.
      Unit is optional and can be `b` (bytes), `k` (kilobytes), `m` (megabytes), or `g` (gigabytes).
    - Ommitting the unit defaults to bytes. If you omit the size entirely, the system uses `64m`.
  default: null

tag:
  description:
    - Image tags. When pulling or pushing, set to 'all' to include all tags.
  default: "latest

ulimit:
  description:
    - List of ulimit options passed to build containers. A ulimit is specified as C(nofile=262144:262144)
  default: null

url:
  description:
    - The location of a Git repository. The repository acts as the context when building an image.
    - Mutually exclusive with path.

state:
  description:
    - Assert the desired state of an image:
    - "absent" - if image exists, unconditionally remove it. Use the force option to untag and remove all images
      matching specified name.
    - "built" - check if image is present. If not found, build using provided parameters. Use force option to always
      build the image.
    - "present" - check if image is present with the provided tag. When not present the image will be pulled from
      Docker Hub or the specified registry. Use the fore option to always pull the image.
    - "pushed" - check if image is present on Docker Hub or the specified registry. If not, push it. Use the force
      option to always push the image.
    - "saved" - save the image to a tar archive. Specify the archive filename with archive_path. Use the force
      option to overwrite an existing archive.
required: false
default: present
choices:
  - absent
  - built
  - present
  - pushed

timeout:
  description:
    - Set image operation timeout.
  default: 600

trust_content:
  description:
    - If true, skip image verification during image build or pull.
  default: false

```


## Returns

```
{
   changed: True
   failed: False
   msg: < text confirming the action that was taken >
   results: {
      < for states built and present include results from docker inspect image >
   }
}
```

## Examples

```
- name: build image
  docker_image:
    path: "/path/to/build/dir"
    name: "my/app"
    state: built
    tags:
      - v1.0
      - mybuild

- name: force pull an image and all tags
  docker_image:
    name: "my/app"
    state: present
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
    state: pushed
    tags: all

- name: pull an image from a registry
  docker_image:
    name: centos
    state: present
    registry: private_registry:8080

```
