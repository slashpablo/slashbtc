"""Small command-line helpers for building reusable development fixtures."""

from __future__ import annotations

import argparse
import os
from pathlib import Path

from dotenv import load_dotenv

from .core import Chain
from .fee import capture_fee_block, fee_summary, save_fee_block


def capture_fee_block_main(argv: list[str] | None = None) -> int:
    """Fetch one Bitcoin Core block and save the compact fee fixture."""
    load_dotenv()
    parser = argparse.ArgumentParser(description="Capture a compact fee fixture from Bitcoin Core RPC.")
    parser.add_argument("height_or_hash", help="Block height or block hash to capture.")
    parser.add_argument("--out", required=True, help="Destination .json or .json.gz fixture path.")
    parser.add_argument("--url", default=os.getenv("BITCOIN_RPC_URL"), help="Bitcoin Core RPC URL.")
    parser.add_argument("--cookie", default=os.getenv("BITCOIN_RPC_COOKIE"), help="Cookie path or raw user:password.")
    parser.add_argument("--rpc-user", default=os.getenv("BITCOIN_RPC_USER"), help="RPC username.")
    parser.add_argument("--rpc-password", default=os.getenv("BITCOIN_RPC_PASSWORD"), help="RPC password.")
    parser.add_argument("--timeout", type=float, default=120.0, help="RPC timeout in seconds.")
    args = parser.parse_args(argv)

    if not args.url:
        parser.error("--url or BITCOIN_RPC_URL is required")

    auth = _rpc_auth(args.cookie, args.rpc_user, args.rpc_password)
    height_or_hash = _height_or_hash(args.height_or_hash)
    with Chain(url=args.url, auth=auth, timeout=args.timeout) as chain:
        block = capture_fee_block(chain, height_or_hash)
    path = save_fee_block(block, args.out)
    summary = fee_summary(block)
    median = summary["percentiles"][50]
    median_text = "n/a" if median is None else f"{median:.2f}"
    print(
        f"saved {path} "
        f"height={summary['height']} "
        f"txs={summary['non_coinbase_tx_count']} "
        f"median={median_text} sat/vB"
    )
    return 0


def _height_or_hash(value: str) -> int | str:
    return int(value) if value.isdigit() else value


def _rpc_auth(
    cookie: str | None,
    rpc_user: str | None,
    rpc_password: str | None,
) -> tuple[str, str] | None:
    if rpc_user and rpc_password:
        return rpc_user, rpc_password
    if not cookie:
        return None

    candidate = Path(cookie).expanduser()
    raw = candidate.read_text().strip() if candidate.exists() else cookie.strip()
    user, sep, password = raw.partition(":")
    if not sep:
        raise ValueError("RPC cookie must be a path or raw user:password string")
    return user, password
