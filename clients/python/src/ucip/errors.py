"""Errors this client raises.

Three classes rather than one, because the three cases call for different
handling and a caller should not have to read a message to tell them apart: the
network never answered, the API answered with a refusal, or a frame was asked
for without the library that builds it. `UcipError` is the base, so a single
`except UcipError` catches everything this package raises and nothing else.
"""

from __future__ import annotations


class UcipError(Exception):
    """Base class for every error this client raises."""


class UcipNetworkError(UcipError):
    """The request never produced a response: DNS, TLS, refused, timed out."""


class UcipHTTPError(UcipError):
    """The API answered with a non-2xx status.

    The status and the API's own message and hint are attributes, so handling
    a 404 does not mean matching on a string.
    """

    def __init__(
        self,
        status: int,
        url: str,
        *,
        detail: str | None = None,
        hint: str | None = None,
        retry_after: float | None = None,
        body: str = "",
    ) -> None:
        summary = detail or body[:200]
        super().__init__(f"UCIP API returned {status} for {url}" + (f": {summary}" if summary else ""))
        self.status = status
        self.url = url
        self.detail = detail
        self.hint = hint
        self.retry_after = retry_after
        self.body = body

    @property
    def is_rate_limited(self) -> bool:
        """True when backing off and retrying is the right response."""
        return self.status == 429


class MissingDependency(UcipError, ImportError):
    """A frame was requested but the library that builds it is not installed.

    Subclasses ImportError as well, so `except ImportError` around an optional
    import still behaves as a reader would expect.
    """
