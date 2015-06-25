'''
decorators.py - function wrappers, basically
'''
from threading import Thread

def async(f):
    '''spawns a new thread when the decorated function is launched'''
    def wrapper(*args, **kwargs):
        thr = Thread(target = f, args = args, kwargs = kwargs)
        thr.start()
    return wrapper
