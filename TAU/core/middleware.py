class DisableHTTPSMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Force the request to use HTTP
        request.is_secure = lambda: False
        request._is_secure = False
        if hasattr(request, 'META'):
            request.META['HTTPS'] = 'off'
            request.META['wsgi.url_scheme'] = 'http'
            if 'HTTP_X_FORWARDED_PROTO' in request.META:
                del request.META['HTTP_X_FORWARDED_PROTO']
        
        response = self.get_response(request)
        return response 