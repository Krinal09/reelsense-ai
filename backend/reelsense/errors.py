"""Typed errors that map cleanly to HTTP responses and frontend messages."""
from __future__ import annotations


class ReelSenseError(Exception):
    status = 400
    code = "error"
    can_use_demo = False

    def __init__(self, message: str, *, details: str | None = None):
        super().__init__(message)
        self.message = message
        self.details = details

    def to_dict(self) -> dict:
        return {
            "code": self.code,
            "message": self.message,
            "details": self.details,
            "can_use_demo": self.can_use_demo,
        }


class InvalidUrl(ReelSenseError):
    status, code = 400, "invalid_url"


class UnsupportedReel(ReelSenseError):
    status, code = 422, "unsupported_reel"
    can_use_demo = True


class CredentialsMissing(ReelSenseError):
    status, code = 503, "credentials_missing"
    can_use_demo = True


class ProviderUnavailable(ReelSenseError):
    status, code = 502, "provider_unavailable"
    can_use_demo = True


class RateLimited(ReelSenseError):
    status, code = 429, "rate_limited"
    can_use_demo = True


class NoComments(ReelSenseError):
    status, code = 422, "no_comments"
    can_use_demo = True


class ProcessingTimeout(ReelSenseError):
    status, code = 504, "processing_timeout"
    can_use_demo = True


class NotFound(ReelSenseError):
    status, code = 404, "not_found"
