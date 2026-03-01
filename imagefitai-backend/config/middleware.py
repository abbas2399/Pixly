class BruteForceCorsMiddleware:
    """
    Adds CORS headers to every response, including error responses from
    Django's own middleware chain (e.g. 500s, 404s). This fires before
    django-cors-headers so OPTIONS preflight always gets a valid reply.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Handle preflight OPTIONS immediately — no need to go deeper
        if request.method == "OPTIONS":
            from django.http import HttpResponse
            response = HttpResponse()
            response.status_code = 200
        else:
            response = self.get_response(request)

        response["Access-Control-Allow-Origin"] = "*"
        response["Access-Control-Allow-Methods"] = "GET, POST, PUT, PATCH, DELETE, OPTIONS"
        response["Access-Control-Allow-Headers"] = (
            "Accept, Accept-Language, Content-Language, Content-Type, "
            "Authorization, X-Requested-With"
        )
        response["Access-Control-Max-Age"] = "86400"
        return response
