---
name: fitting-ai
description: Virtual clothing try-on with Replicate cuuupid/idm-vton. Use when the user wants to preview a garment on a person photo. Requires REPLICATE_API_TOKEN.
---

# Fitting AI

Use this skill when the user asks for virtual clothing fitting, try-on, outfit preview, or IDM-VTON generation.

## Requirements

1. [Replicate API token](https://replicate.com/account/api-tokens)
2. `.env` in the **plugin root** (folder containing `.codex-plugin/`):

```bash
cp .env.example .env
# REPLICATE_API_TOKEN=r8_...
```

In this repo the plugin root is `src/`. After Codex install, use the cached plugin folder or set `REPLICATE_API_TOKEN` in the environment.

Always run commands from the plugin root.

## Web UI

```bash
python scripts/serve.py
```

Open `http://127.0.0.1:8765`. Run in the background if the session should stay interactive.

## CLI

```bash
python scripts/try_on.py --human person.jpg --garment shirt.jpg --category upper_body --out result.jpg
```

`category`: `upper_body` | `lower_body` | `dresses`

## Notes

- Model: `cuuupid/idm-vton` on Replicate
- Do not claim the result is saved unless `--out` was used or the user downloaded from the UI
