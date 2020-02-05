#!/usr/bin/env bash
"$1" 100 & 
echo "$!" > "$2"
