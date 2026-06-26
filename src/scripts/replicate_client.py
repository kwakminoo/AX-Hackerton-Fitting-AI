#!/usr/bin/env python3
"""Replicate cuuupid/idm-vton client — stdlib only."""
import base64
import json
import mimetypes
import os
import time
import urllib.error
import urllib.request
from pathlib import Path

MODEL_OWNER = "cuuupid"
MODEL_NAME = "idm-vton"
# ponytail: pinned fallback when version lookup fails
FALLBACK_VERSION = "d73e611d73581af0410fc0b5cc400e2cae959a92cb6c8b54d6ad102c52b4d5ab"
_version_cache: str | None = None
API = "https://api.replicate.com/v1"
POLL_SEC = 2
POLL_MAX = 120
_PLACEHOLDER = "r8_your_token_here"
_dotenv_loaded = False


def _plugin_root() -> Path:
    """Codex sets PLUGIN_ROOT; repo dev uses src/ next to scripts/."""
    root = os.environ.get("PLUGIN_ROOT", "").strip()
    if root:
        return Path(root)
    return Path(__file__).resolve().parent.parent


def load_dotenv() -> None:
    """Load plugin-root .env (src/.env in repo, .env in Codex cache). utf-8-sig for Windows BOM."""
    global _dotenv_loaded
    env_path = _plugin_root() / ".env"
    if env_path.is_file():
        for line in env_path.read_text(encoding="utf-8-sig").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, _, v = line.partition("=")
            k, v = k.strip(), v.strip().strip('"').strip("'")
            if k and v and v != _PLACEHOLDER:
                os.environ[k] = v
    _dotenv_loaded = True


def token_configured() -> bool:
    load_dotenv()
    t = os.environ.get("REPLICATE_API_TOKEN", "").strip()
    return bool(t) and t != _PLACEHOLDER


def _token() -> str:
    load_dotenv()
    t = os.environ.get("REPLICATE_API_TOKEN", "").strip()
    if not t or t == _PLACEHOLDER:
        raise RuntimeError(
            "REPLICATE_API_TOKEN 환경변수를 설정하세요. "
            "플러그인 루트의 .env (src/.env) 에 토큰을 넣거나 환경변수로 설정하세요."
        )
    return t


def _data_uri(data: bytes, mime: str = "image/jpeg") -> str:
    return f"data:{mime};base64,{base64.b64encode(data).decode()}"


def _guess_mime(path: str | None, data: bytes) -> str:
    if path:
        mt, _ = mimetypes.guess_type(path)
        if mt:
            return mt
    return "image/jpeg" if data[:3] == b"\xff\xd8\xff" else "image/png"


def _api(method: str, path: str, body: dict | None = None, *, timeout: int = 60) -> dict:
    headers = {
        "Authorization": f"Bearer {_token()}",
        "Content-Type": "application/json",
    }
    if method == "POST":
        headers["Prefer"] = "wait"
    req = urllib.request.Request(
        f"{API}{path}",
        data=json.dumps(body).encode() if body is not None else None,
        headers=headers,
        method=method,
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        detail = e.read().decode(errors="replace")
        raise RuntimeError(f"Replicate API 오류 ({e.code}): {detail}") from e


def _model_version() -> str:
    """Community models use POST /predictions + version (not /models/.../predictions)."""
    global _version_cache
    if _version_cache:
        return _version_cache
    try:
        data = _api("GET", f"/models/{MODEL_OWNER}/{MODEL_NAME}")
        vid = (data.get("latest_version") or {}).get("id")
        if vid:
            _version_cache = vid
            return vid
    except RuntimeError:
        pass
    _version_cache = FALLBACK_VERSION
    return FALLBACK_VERSION


def run(
    human: bytes,
    garment: bytes,
    *,
    human_name: str | None = None,
    garment_name: str | None = None,
    category: str = "upper_body",
    garment_des: str = "clothing",
    crop: bool = True,
) -> str:
    """Return output image URL from IDM-VTON."""
    payload = {
        "version": _model_version(),
        "input": {
            "human_img": _data_uri(human, _guess_mime(human_name, human)),
            "garm_img": _data_uri(garment, _guess_mime(garment_name, garment)),
            "category": category,
            "garment_des": garment_des,
            "crop": crop,
        },
    }
    pred = _api("POST", "/predictions", payload, timeout=120)
    st = pred.get("status")
    if st in ("succeeded", "successful"):
        out = pred.get("output")
        if isinstance(out, str) and out:
            return out

    pred_id = pred.get("id")
    if not pred_id:
        raise RuntimeError(f"예측 ID 없음: {pred}")

    deadline = time.monotonic() + POLL_MAX
    while time.monotonic() < deadline:
        status = _api("GET", f"/predictions/{pred_id}")
        st = status.get("status")
        if st in ("succeeded", "successful"):
            out = status.get("output")
            if isinstance(out, str) and out:
                return out
            raise RuntimeError(f"출력 없음: {status}")
        if st in ("failed", "canceled"):
            raise RuntimeError(status.get("error") or f"예측 {st}")
        time.sleep(POLL_SEC)

    raise RuntimeError("Replicate 응답 시간 초과")


if __name__ == "__main__":
    # ponytail: minimal self-check — token 없으면 skip
    assert _guess_mime("x.jpg", b"\xff\xd8\xff\x00") == "image/jpeg"
    assert _data_uri(b"ab").startswith("data:image/jpeg;base64,")
    if os.environ.get("REPLICATE_API_TOKEN"):
        print("replicate_client: token set, self-check OK")
    else:
        print("replicate_client: self-check OK (token skip)")
