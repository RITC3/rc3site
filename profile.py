#!flask/bin/python
from werkzeug.contrib.profiler import ProfilerMiddleware
from app import app
import sys

if len(sys.argv) == 1:
    num=10
else:
    num=sys.argv[1]

app.config['PROFILE'] = True
app.wsgi_app = ProfilerMiddleware(app.wsgi_app, restrictions=[int(num)])
if __name__ == '__main__':
	app.run(host='0.0.0.0', debug = True)
