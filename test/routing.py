
class Plugin:
    def __init__(self):
        self.handle = 'test runner'
        self.args = []

    def route(self, path):
        def decorator(func):
            return func
        return decorator

    def url_for(self, func, *args, **kwargs):
        return {
            'func': func.__name__,
            'args': kwargs
        }
