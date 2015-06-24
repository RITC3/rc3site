'''
decorators.py - function wrappers, basically
'''
from threading import Thread

#spawns a new thread when the decorated function is launched
def async(f):
    def wrapper(*args, **kwargs):
        thr = Thread(target = f, args = args, kwargs = kwargs)
        thr.start()
    return wrapper
