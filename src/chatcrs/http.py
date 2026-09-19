"""HTTP transport policy shared by every ChatCRS network entry point.

Use the caller's exact URL, never environment/OS proxies, redirects or retries.
The standard HTTPS handler retains certificate and hostname verification.
"""
from __future__ import annotations

import urllib.request


class NoRedirectHandler(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        # Even same-origin redirects can replay a write or change its endpoint.
        return None


def open_request(request: urllib.request.Request, *, timeout: float):
    """Open once with default TLS verification and no implicit routing."""
    opener = urllib.request.build_opener(
        urllib.request.ProxyHandler({}), NoRedirectHandler(),
    )
    return opener.open(request, timeout=timeout)
