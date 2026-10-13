#!/usr/bin/env python3
"""tests/test_identity.py — selftest for the proposed identity layer (stdlib only).

Run: python tests/test_identity.py   (exit 0 = pass)
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "radar"))
from identity import normalize, fingerprint, dedupe_names, identity_counts  # noqa: E402


def main() -> int:
    fails = []
    # 1. same identity across separators/case/fullwidth
    g = [normalize(x) for x in ("DeepSeek-V3.2", "deepseek_v3.2", "DEEPSEEK V3.2", "deepseek.v3.2")]
    if len({fingerprint(x) for x in g}) != 1:
        fails.append(f"separator normalization: {g}")
    # 2. version numbers are identity (GLM-5 != GLM-6)
    if fingerprint(normalize("GLM-5")) == fingerprint(normalize("GLM-6")):
        fails.append("version identity broken")
    # 3. zh alias -> en identity
    if fingerprint(normalize("深度求索-V3.2")) != fingerprint(normalize("deepseek-v3.2")):
        fails.append("zh alias broken")
    # 4. dedupe keeps first canonical spelling, order stable
    d = dedupe_names(["DeepSeek-V3.2", "deepseek_v3.2", "GLM-5", "glm 5"])
    if len(d) != 2 or d[0] != "DeepSeek-V3.2":
        fails.append(f"dedupe: {d}")
    # 5. identity_counts aggregates
    c = identity_counts(["glm-5", "GLM 5", "glm-6"])
    if c.get("glm-5") != 2 or c.get("glm-6") != 1:
        fails.append(f"counts: {c}")
    # 6. family level (strip version)
    if normalize("Qwen3-Max", keep_version=False) != normalize("qwen 3 max", keep_version=False):
        fails.append("family level broken")
    # 7. empty safety
    if normalize("   ") != "":
        fails.append("empty safety")
    if fails:
        print("FAIL:")
        [print("  -", x) for x in fails]
        return 1
    print("identity layer selftest: 7/7 PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
