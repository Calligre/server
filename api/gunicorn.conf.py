import multiprocessing
import os


bind = '0.0.0.0:8080'
daemon = True
pidfile = 'api.pid'

workers = threads = 2 * multiprocessing.cpu_count() + 1

accesslog = 'api.access.log'
errorlog = 'api.error.log'

# require these to be set in production
_ = os.environ['DB_BASE']
_ = os.environ['DB_HOST']
_ = os.environ['DB_PASS']
_ = os.environ['DB_PORT']
_ = os.environ['DB_USER']
