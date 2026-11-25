"""Runtime configuration. Everything comes from environment variables
(Vercel project settings in production, `.env` locally). Values are read at
call time so nothing is cached between serverless invocations."""
from __future__ import annotations

import os
from pathlib import Path


def _load_dotenv() -> None:
    """Read <project>/.env (also .env.txt / env.txt, which Windows often creates) so tokens work
    however the server is started."""
    root = Path(__file__).resolve().parents[2]
    for name in (".env", ".env.txt", "env.txt"):
        f = root / name
        if not f.exists():
            continue
        for line in f.read_text(encoding="utf-8-sig").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                v = v.strip().strip('"').strip("'")
                if v:
                    os.environ.setdefault(k.strip(), v)


_load_dotenv()


def _get(*names: str, default: str | None = None) -> str | None:
    for n in names:
        v = os.environ.get(n)
        if v:
            return v
    return default


class Settings:
    # --- Apify (default live provider: works for any public Reel, no user login) ---
    @property
    def apify_token(self): return _get("APIFY_TOKEN", "APIFY_API_TOKEN")
    @property
    def apify_reel_actor(self): return _get("APIFY_REEL_ACTOR", default="apify~instagram-reel-scraper")
    @property
    def apify_comment_actor(self): return _get("APIFY_COMMENT_ACTOR", default="apify~instagram-comment-scraper")
    @property
    def apify_include_replies(self): return _get("APIFY_INCLUDE_REPLIES", default="false").lower() == "true"
    @property
    def live_provider(self): return _get("LIVE_PROVIDER", default="auto")  # auto | apify | graph

    # --- Instagram Graph API (official, own account only) ---
    @property
    def ig_access_token(self): return _get("IG_ACCESS_TOKEN")
    @property
    def ig_user_id(self): return _get("IG_USER_ID")
    @property
    def graph_version(self): return _get("IG_GRAPH_VERSION", default="v21.0")

    # --- Optional result store (Upstash Redis / Vercel KV REST) ---
    @property
    def kv_url(self): return _get("KV_REST_API_URL", "UPSTASH_REDIS_REST_URL")
    @property
    def kv_token(self): return _get("KV_REST_API_TOKEN", "UPSTASH_REDIS_REST_TOKEN")

    # --- Limits ---
    @property
    def max_comments(self): return int(_get("MAX_COMMENTS", default="300"))
    @property
    def time_budget_s(self): return float(_get("TIME_BUDGET_SECONDS", default="150"))
    @property
    def result_ttl_s(self): return int(_get("RESULT_TTL_SECONDS", default="86400"))


settings = Settings()
