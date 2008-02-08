from paste.debug.profile import profile_decorator

class OKView:
    def __init__(self, context, request):
        self.context = context
        self.request = request

    def __call__(self):
        return 'OK'
