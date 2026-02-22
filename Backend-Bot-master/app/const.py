HTTP_ERROR_MESSAGES = {
    500: ("UNKNOWN",),
    400: ("VALIDATION_ERROR", "VALIDATION_ERROR_MAIL", "VALIDATION_ERROR_PHONE",),
    401: ("UNAUTHORIZED", "CODE_EXPIRED", "CODE_INVALID"),
    403: ("FORBIDDEN", "DRIVER_PROFILE_NOT_APPROVED"),
    404: ("NOT_FOUND",),
    409: ("CONFLICT",),
    429: ("RATE_LIMIT_EXCEEDED",),
}

def get_swagger_page(auth_header: str = ""):
    return f"""<!DOCTYPE html>
<html>
  <head>
    <link type="text/css" rel="stylesheet" href="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css">
    <link rel="shortcut icon" href="https://fastapi.tiangolo.com/img/favicon.png">
    <title>API docs</title>
  </head>
  <body>
    <div id="swagger-ui"></div>
    <script src="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js"></script>
    <script>
      window.onload = () => {{
        const ui = SwaggerUIBundle({{
          url: '/openapi.json',
          dom_id: '#swagger-ui',
          presets: [
            SwaggerUIBundle.presets.apis,
            SwaggerUIBundle.SwaggerUIStandalonePreset,
          ],
          layout: 'BaseLayout',
          persistAuthorization: true,
          requestInterceptor: (req) => {{
            req.headers = req.headers || {{}};
            if (!req.headers['Authorization'] && !req.headers['authorization']) {{
              req.headers['Authorization'] = {auth_header!r};
            }}
            return req;
          }},
        }});
        window.ui = ui;
      }};
    </script>
  </body>
</html>"""
