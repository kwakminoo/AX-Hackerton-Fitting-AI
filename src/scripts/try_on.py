#!/usr/bin/env python3
"""CLI virtual try-on."""
import argparse
import os
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from replicate_client import load_dotenv, run  # noqa: E402


def main() -> int:
    load_dotenv()
    p = argparse.ArgumentParser(description="Fitting AI — virtual try-on CLI")
    p.add_argument("--human", required=True, help="사용자 사진 경로")
    p.add_argument("--garment", required=True, help="옷 사진 경로")
    p.add_argument("--category", default="upper_body", choices=["upper_body", "lower_body", "dresses"])
    p.add_argument("--out", help="저장 경로 (지정 시에만 파일 저장)")
    args = p.parse_args()

    human_path = Path(args.human)
    garment_path = Path(args.garment)
    if not human_path.is_file():
        print(f"파일 없음: {human_path}", file=sys.stderr)
        return 1
    if not garment_path.is_file():
        print(f"파일 없음: {garment_path}", file=sys.stderr)
        return 1

    url = run(
        human_path.read_bytes(),
        garment_path.read_bytes(),
        human_name=human_path.name,
        garment_name=garment_path.name,
        category=args.category,
    )
    print(url)

    if args.out:
        urllib.request.urlretrieve(url, args.out)
        print(f"저장: {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
