#!flask/bin/python
from werkzeug.contrib.profiler import ProfilerMiddleware
from app import app
import sys

app.config['PROFILE'] = True
app.wsgi_app = ProfilerMiddleware(app.wsgi_app, restrictions=[int(sys.argv[1])])
if __name__ == '__main__':
	app.run(host='0.0.0.0', debug = True)
