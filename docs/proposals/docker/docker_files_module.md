# docker_files modules proposal

## Purpose and Scope

The purpose of docker_files is to provide an interface to the Docker cp and diff commands. Similar to `docker cp`,
docker_files will provide a mechanism to copy files between the local file system and the container's file system.
And similar to `docker diff`, docker_files will provide a mechanism to retrieve a list of changed from the container's
file system.

## Parameters

Docker_files accepts the parameters listed below. diff is mutually exclusive of dst, src and follow_link. dest and src
are required to perform a copy.

```
diff:
  description:
    - Provide a list of container names or IDs. For each container a list of changed files and directories found on the
      container's file system will be returned.
  default: null

dest:
  description:
    - Destination path of copied files. If the destination is a container file system, precede the path with a
      container name or ID + ':'. For example, C(mycontainer:/path/to/file.txt). If the destination path does not exist,
      it will be created. If the destination path exists and is a file, it will be overwritten.
  default: null

src:
  description:
    - The source path of file(s) to be copied. If source files are found on the container's file system, precede the
      path with the container name or ID + ':'. For example, C(mycontainer:/path/to/files).
  default: null

follow_link:
  description:
    - Follow symbolic links in the src path. If src is local and is a symbolic link, the symbolic link, not the target
    is copied by default. To copy the link target and no the link, set follow_link to true.
  default: false

event_type:
  description:
    - Select the specific event type to list in the diff output.
  choices:
    - all
    - add
    - delete
    - change
  default: all
```

## Examples

```
- name: Copy files from the local file system to a container's file system
  docker_files:
    src: /tmp/rpm
    dest: mycontainer:/tmp
    follow_links: yes

- name: List all differences for multiple containers.
  docker_files:
    diff:
      - mycontainer1
      - mycontainer2

- name: Included changed files only in diff output
  docker_files:
    diff:
      - mycontainer1
    event_type: change
```

## Returns

Returned from diff:

```
{
    changed: false,
    failed: false,
    rc: 0,
    results: {
        mycontainer1: [
            { state: 'C', path: '/dev' },
            { state: 'A', path: '/dev/kmsg' },
            { state: 'C', path: '/etc' },
            { state: 'A', path: '/etc/mtab' }
        ],
        mycontainer2: [
            { state: 'C', path: '/foo' },
            { state: 'A', path: '/foo/bar.txt' }
        ]
    }
}
```

Returned from cp:

```
{
    changed: true,
    failed: false,
    rc: 0,
    results: {
        src: /tmp/rpms,
        dest: mycontainer:/tmp
        files_copied: [
            'file1.txt',
            'file2.jpg'
        ]
    }
}
```
