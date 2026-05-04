from io import BytesIO

import matplotlib

matplotlib.use("Agg")

from slashbtc.fee import FeeBlock, fee_histogram, fee_summary, load_fee_block, save_fee_block
from slashbtc.samples import sample_fee_block, sample_fee_block_names
from slashbtc.viz import fee_distribution_chart


def test_synthetic_modern_busy_is_rich_enough_for_fee_chart():
    block = sample_fee_block("synthetic_modern_busy")
    summary = fee_summary(block)

    assert summary["non_coinbase_tx_count"] == 2847
    assert 10 <= summary["percentiles"][50] <= 30
    assert summary["percentiles"][99] > summary["percentiles"][90]
    assert summary["overpayment_tail"]["tx_count"] > 100


def test_zero_fee_era_remains_available_as_edge_case():
    block = sample_fee_block("synthetic_zero_fee_era")
    summary = fee_summary(block)

    assert summary["non_coinbase_tx_count"] == 3
    assert summary["percentiles"][50] == 0
    assert summary["clearing_fee_sat_vb"] == 0
    assert summary["overpayment_tail"]["tx_count"] == 0


def test_fee_histogram_has_overflow_bucket():
    block = sample_fee_block("synthetic_congestion_tail")
    buckets = fee_histogram(block, max_sat_vb=200)

    assert buckets[-1]["bucket_lower_sat_vb"] == 200
    assert buckets[-1]["bucket_upper_sat_vb"] is None
    assert buckets[-1]["tx_count"] > 0


def test_compact_fee_block_round_trip(tmp_path):
    original = sample_fee_block("synthetic_calm")
    path = save_fee_block(original, tmp_path / "calm.json.gz")
    loaded = load_fee_block(path)

    assert isinstance(loaded, FeeBlock)
    assert loaded.to_record() == original.to_record()


def test_packaged_real_samples_are_discoverable():
    names = sample_fee_block_names()

    assert "mainnet_zero_fee_100000" in names
    assert "mainnet_recent_947663" in names
    assert sample_fee_block("mainnet_recent_947663").txs


def test_fee_distribution_chart_renders_nonblank_png():
    block = sample_fee_block("synthetic_modern_busy")
    fig = fee_distribution_chart(block)
    buf = BytesIO()

    fig.savefig(buf, format="png")

    assert buf.tell() > 10_000
