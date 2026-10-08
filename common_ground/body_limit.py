from starlette.responses import JSONResponse


class BodyLimitMiddleware:
    """Bound actual streamed API bodies, not merely the advertised Content-Length."""

    def __init__(self, app, limit=16384):
        self.app = app
        self.limit = limit

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http" or not scope["path"].startswith("/api/"):
            return await self.app(scope, receive, send)
        body = bytearray()
        while True:
            event = await receive()
            if event["type"] == "http.disconnect":
                return
            body.extend(event.get("body", b""))
            if len(body) > self.limit:
                return await JSONResponse(
                    {"detail": "Request too large."},
                    status_code=413,
                    headers={"Cache-Control": "no-store"},
                )(scope, receive, send)
            if not event.get("more_body", False):
                break
        replayed = False

        async def replay():
            nonlocal replayed
            if not replayed:
                replayed = True
                return {"type": "http.request", "body": bytes(body), "more_body": False}
            return await receive()

        return await self.app(scope, replay, send)
