#!/usr/bin/env python3
"""radar/identity.py — optional term-identity layer for new-term-radar.

Proposal PR (from chenhz01/termledger, MIT): resolve the same model's many
spellings into ONE identity before counting, so the daily report doesn't
inflate "DeepSeek-V3.2 / deepseek_v3.2 / 深度求索V3" into three trends.

- stdlib-only, no new dependencies, deterministic (same input -> same output)
- version numbers are part of identity: GLM-5 != GLM-6 (key negative case)
- zh-CN alias map supported, extensible via radar's config
- opt-in: nothing in the existing pipeline changes unless you call it

MIT licensed, consistent with this repo. Vendored core from
https://github.com/chenhz01/termledger (also MIT) so this PR stays
self-contained; happy to switch to a dependency or shrink the diff as
maintainers prefer.
"""
from __future__ import annotations
import hashlib, re, unicodedata

_WS = re.compile(r"[\s\-_.]+")
_VER_TAIL = re.compile(r"-?(?:v-)?\d+(?:-\d+)*$", re.IGNORECASE)
_BOUND1 = re.compile(r"(?<=[a-z0-9])(?=[A-Z])")
_BOUND2 = re.compile(r"(?<=[A-Za-z])(?=\d)|(?<=\d)(?=[A-Za-z])")

DEFAULT_ALIAS = {
    "深度求索": "deepseek", "ds": "deepseek",
    "通义千问": "qwen", "千问": "qwen",
    "智谱": "zhipu", "清华智谱": "zhipu",
}


def _key(s: str) -> str:
    return re.sub(r"[\s\-_.]+", "", s.lower())


def normalize(term: str, alias: dict[str, str] | None = None,
              keep_version: bool = True) -> str:
    """NFKC -> word-boundary split -> lowercase -> unified separator -> alias -> version policy.

    alias=None falls back to the built-in DEFAULT_ALIAS; pass {} to disable aliases.
    """
    if not term or not term.strip():
        return ""
    if alias is None:
        alias = DEFAULT_ALIAS
    t = unicodedata.normalize("NFKC", term).strip()
    t = _BOUND2.sub(" ", _BOUND1.sub(" ", t))
    t = _WS.sub("-", t.lower()).strip("-")
    if alias:
        key = _key(t)
        if key in alias:
            t = _WS.sub("-", unicodedata.normalize("NFKC", alias[key]).lower()).strip("-")
        else:
            m = _VER_TAIL.search(t)
            if m:
                root_key = _key(t[:m.start()])
                if root_key and root_key in alias:
                    root = _WS.sub("-", unicodedata.normalize("NFKC", alias[root_key]).lower()).strip("-")
                    t = root + m.group(0)
    if not keep_version:
        t = _VER_TAIL.sub("", t).strip("-")
    return t


def fingerprint(norm: str) -> str:
    """Deterministic identity fingerprint (hash of separator-free key)."""
    k = _key(norm) if norm else ""
    return hashlib.sha1(k.encode("utf-8")).hexdigest()[:12] if k else ""


def dedupe_names(names: list[str], alias: dict[str, str] | None = None) -> list[str]:
    """Collapse alias spellings: first-seen canonical form wins, count-preserving order."""
    out: dict[str, str] = {}
    for raw in names:
        n = normalize(raw, alias)
        if n and _key(n) not in out:
            out[_key(n)] = raw
    return list(out.values())


def identity_counts(names: list[str], alias: dict[str, str] | None = None) -> dict[str, int]:
    """Count by canonical identity instead of raw spelling."""
    counts: dict[str, int] = {}
    for raw in names:
        n = normalize(raw, alias)
        if n:
            counts[n] = counts.get(n, 0) + 1
    return dict(sorted(counts.items(), key=lambda kv: -kv[1]))
