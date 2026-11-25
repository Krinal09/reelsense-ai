from .apify import ApifyProvider
from .base import ReelProvider
from .graph_api import GraphApiProvider
from .mock import MockProvider
from ..config import settings


def get_provider(mode: str, apify_token: str | None = None) -> ReelProvider:
    """`demo` is kept for tests/dev only (not exposed in the UI)."""
    if mode == "demo":
        return MockProvider()
    if apify_token:
        return ApifyProvider(apify_token)
    choice = settings.live_provider
    if choice == "graph":
        return GraphApiProvider()
    if choice == "apify" or settings.apify_token:
        return ApifyProvider()
    if settings.ig_access_token and settings.ig_user_id:
        return GraphApiProvider()
    return ApifyProvider()  # raises a clear "APIFY_TOKEN missing" error on fetch


__all__ = ["ReelProvider", "ApifyProvider", "GraphApiProvider", "MockProvider", "get_provider"]
