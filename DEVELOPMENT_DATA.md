# Development Data

`slashbtc` keeps live Bitcoin Core RPC on the edge of the workflow. The
visualization layer works against compact `FeeBlock` objects, so notebooks,
tests, and design iteration can run without a node.

## Default path

```python
from slashbtc.samples import sample_fee_block
from slashbtc.viz import fee_distribution_chart

block = sample_fee_block("synthetic_modern_busy")
fig = fee_distribution_chart(block)
```

Synthetic samples are deterministic and cover useful shapes:

- `synthetic_modern_busy`: dense modern block with a visible fee tail.
- `synthetic_calm`: low-fee market with a small tail.
- `synthetic_congestion_tail`: high-fee stress case with a 200+ sat/vB overflow bucket.
- `synthetic_zero_fee_era`: block-100,000-style zero-fee edge case.
- `synthetic_empty`: coinbase-only edge case.

## Real specimens

Packaged real-mainnet fixtures are compact summaries derived from Bitcoin Core
`getblock` verbosity `3` responses. They keep only the fields needed for fee
distribution work: block identity, timestamp, transaction count, virtual size,
and fee sats.

- `mainnet_zero_fee_100000`: confirms the early-chain zero-fee behavior.
- `mainnet_recent_947663`: recent mainnet block with enough fee variety for chart work.

## Refreshing fixtures

Use live RPC only when minting or refreshing a specimen:

```sh
slashbtc-capture-fee-block 947663 \
  --out slashbtc/data/fee_blocks/mainnet_recent_947663.json.gz
```

The command reads `BITCOIN_RPC_URL` and `BITCOIN_RPC_COOKIE` from `.env`, or you
can pass `--url`, `--cookie`, `--rpc-user`, and `--rpc-password` explicitly.
