import os

# Server socket
bind = "0.0.0.0:" + os.environ.get("PORT", "8080")
backlog = 2048

# Worker processes
workers = 1
worker_class = 'sync'
worker_connections = 1000
timeout = 120  # Increase timeout for potentially slow API responses
keepalive = 2

# Server mechanics
daemon = False
raw_env = []
pidfile = None
umask = 0
user = None
group = None

# Logging
errorlog = '-'
loglevel = 'info'
accesslog = '-'
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'

# Process naming
proc_name = None
default_proc_name = 'server:app' 