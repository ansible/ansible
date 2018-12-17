#!/usr/bin/env bash
$1 100 & 
echo $! > newpid.txt
