# Docker_Files Modules Proposal

## Purpose and Scope

The purpose of docker_files is to provide for retrieving a file or folder from a container's file system, 
inserting a file or folder into a container, exporting a container's entire filesystem as a tar archive, or 
retrieving a list of changed files from a container's file system.

Docker_files will manage a container using docker-py to communicate with either a local or remote API. It will
support API versions >= 1.14. API connection details will be handled externally in a shared utility module similar to
how other cloud modules operate.

## Parameters

Docker_files accepts the parameters listed below. API connection parameters will be part of a shared utility module
as mentioned above.

```
diff:
  description:
    - Provide a list of container names or IDs. For each container a list of changed files and directories found on the
      container's file system will be returned. Diff is mutually exclusive from all other options except event_type. 
      Use event_type to choose which events to include in the output.
  default: null

export:
  description: 
    - Provide a container name or ID. The container's file system will be exported to a tar archive. Use dest
      to provide a path for the archive on the local file system. If the output file already exists, it will not be
      overwritten. Use the force option to overwrite an existing archive.
  default: null
  
dest:
  description:
    - Destination path of copied files. If the destination is a container file system, precede the path with a
      container name or ID + ':'. For example, C(mycontainer:/path/to/file.txt). If the destination path does not
      exist, it will be created. If the destination path exists on a the local filesystem, it will not be overwritten.
      Use the force option to overwrite existing files on the local filesystem.
  default: null

force: 
  description:
    - Overwrite existing files on the local filesystem. 
  default: false
  
follow_link:
  description:
    - Follow symbolic links in the src path. If src is local and file is a symbolic link, the symbolic link, not the 
    target is copied by default. To copy the link target and not the link, set follow_link to true.
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

src:
  description:
    - The source path of file(s) to be copied. If source files are found on the container's file system, precede the
      path with the container name or ID + ':'. For example, C(mycontainer:/path/to/files).
  default: null

```

## Examples

```
- name: Copy files from the local file system to a container's file system
  docker_files:
    src: /tmp/rpm
    dest: mycontainer:/tmp
    follow_links: yes

- name: Copy files from the container to the local filesystem and overwrite existing files
  docker_files:
    src: container1:/var/lib/data
    dest: /tmp/container1/data
    force: yes
    
- name: Export container filesystem
  docker_file:
    export: container1
    dest: /tmp/conainer1.tar
    force: yes
    
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

Returned when copying files:

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

Return when exporting container filesystem:

```
{
   changed: true,
    failed: false,
    rc: 0,
    results: {
        src: container_name,
        dest: local/path/archive_name.tar
    }
}

```
