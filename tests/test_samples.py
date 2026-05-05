from io import BytesIO

import matplotlib

matplotlib.use("Agg")

from slashbtc.samples import (
    load_sample_block,
    sample_block,
    sample_block_names,
    sample_blocks,
    sample_to_db_rows,
    save_sample_block,
)
from slashbtc.viz import fee_distribution_chart, transaction_fee_histogram, transaction_fee_summary


DB_TRANSACTION_FIELDS = {
    "txid",
    "wtxid",
    "position_in_block",
    "version",
    "locktime",
    "size_bytes",
    "vsize_vb",
    "weight_wu",
    "input_count",
    "output_count",
    "input_value_sats",
    "output_value_sats",
    "fee_sats",
    "fee_sat_vb",
    "is_coinbase",
    "has_witness",
}


def test_synthetic_sample_is_db_shaped():
    sample = sample_block("synthetic_modern_busy")
    block, rows = sample_to_db_rows(sample)

    assert {"hash", "height", "time"} <= set(block)
    assert len(rows) == 2848
    assert rows[0]["is_coinbase"] is True
    assert rows[1]["is_coinbase"] is False
    assert DB_TRANSACTION_FIELDS <= set(rows[1])


def test_sample_set_covers_architecture_cases():
    samples = sample_blocks()
    names = {sample["name"] for sample in samples}

    assert "synthetic_empty" in names
    assert "synthetic_zero_fee_era" in names
    assert "synthetic_congestion_tail" in names


def test_zero_fee_era_remains_an_edge_case():
    rows = sample_block("synthetic_zero_fee_era")["transactions"]
    summary = transaction_fee_summary(rows)

    assert summary["non_coinbase_tx_count"] == 3
    assert summary["percentiles"][50] == 0
    assert summary["clearing_fee_sat_vb"] == 0
    assert summary["overpayment_tail"]["tx_count"] == 0


def test_fee_histogram_has_overflow_bucket_from_db_rows():
    rows = sample_block("synthetic_congestion_tail")["transactions"]
    buckets = transaction_fee_histogram(rows, max_sat_vb=200)

    assert buckets[-1]["bucket_lower_sat_vb"] == 200
    assert buckets[-1]["bucket_upper_sat_vb"] is None
    assert buckets[-1]["tx_count"] > 0


def test_sample_block_round_trip(tmp_path):
    original = sample_block("synthetic_calm")
    path = save_sample_block(original, tmp_path / "calm.json.gz")
    loaded = load_sample_block(path)

    assert loaded == original


def test_packaged_real_samples_are_discoverable():
    names = sample_block_names()
    recent = sample_block("mainnet_recent_947663")

    assert "mainnet_zero_fee_100000" in names
    assert "mainnet_recent_947663" in names
    assert recent["block"]["height"] == 947663
    assert len(recent["transactions"]) > 100


def test_fee_distribution_chart_renders_nonblank_png():
    rows = sample_block("synthetic_modern_busy")["transactions"]
    fig = fee_distribution_chart(rows)
    buf = BytesIO()

    fig.savefig(buf, format="png")

    assert buf.tell() > 10_000
