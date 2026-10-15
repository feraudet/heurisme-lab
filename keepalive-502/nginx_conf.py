#!/usr/bin/env python3
"""Writes the nginx configuration of the bench on stdout.

usage: python3 nginx_conf.py <upstream keepalive_timeout> <number of lanes>

One lane = one nginx port (8000 + n) in front of one Node.js port (3000 + n), with its own
pool of idle connections. The lanes run side by side so that the bench sees more requests in
the same time; they share nothing.
"""
import sys

timeout, lanes = sys.argv[1], int(sys.argv[2])

print(f"""worker_processes 1;
pid /w/run/nginx.pid;
error_log /w/run/error.log error;
events {{ worker_connections 1024; }}
http {{
  access_log off;
  log_format lane '$request_method $status upstream=$upstream_status';
""")
for n in range(lanes):
    print(f"""  upstream api_{n} {{
    server 127.0.0.1:{3000 + n};
    keepalive 4;
    keepalive_timeout {timeout};
  }}
  server {{
    listen 127.0.0.1:{8000 + n};
    access_log /w/run/access.log lane;
    location / {{
      proxy_pass http://api_{n};
      proxy_http_version 1.1;
      proxy_set_header Connection "";
    }}
  }}""")
print("}")
