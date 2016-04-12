#!flask/bin/python
from app import app
from argparse import ArgumentParser

def parse_and_run(args=None):
    p = ArgumentParser()
    p.add_argument('--bind', '-b', action='store', help='the address to bind to', default='127.0.0.1')
    p.add_argument('--port', '-p', action='store', type=int, help='the port to listen on', default=8080)
    p.add_argument('--debug', '-d', action='store_true', help='enable debugging (use with caution)', default=False)
    args = p.parse_args(args)
    app.run(host=args.bind, port=args.port, debug=args.debug)

if __name__ == '__main__':
    parse_and_run()
