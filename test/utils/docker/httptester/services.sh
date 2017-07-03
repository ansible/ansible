#!/bin/sh
gunicorn -D httpbin:app
nginx -g "daemon off;"
