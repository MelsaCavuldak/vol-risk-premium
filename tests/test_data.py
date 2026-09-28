import pandas as pd
import pytest

from vrp.data import load_market_data
from vrp.report import as_percent, markdown_table


def write_prices(path, values, adjusted=False):
    dates = pd.bdate_range("2024-01-02", periods=len(values))
    frame = pd.DataFrame({"Date": dates.strftime("%Y-%m-%d"), "Close": values})
    if adjusted:
        frame["Adj Close"] = [v * 2 for v in values]
    frame.to_csv(path, index=False)


def test_csv_loader_aligns_and_filters(tmp_path):
    write_prices(tmp_path / "spx.csv", [4700.0, 4720.0, 4690.0, 4750.0])
    write_prices(tmp_path / "vix.csv", [13.0, 12.5, 0.0, 12.0])
    data = load_market_data("csv", "2024-01-01", spx_csv=tmp_path / "spx.csv", vix_csv=tmp_path / "vix.csv")
    assert list(data.columns) == ["spx", "vix"]
    assert len(data) == 3
    assert (data > 0).all().all()


def test_csv_loader_prefers_adjusted_close(tmp_path):
    write_prices(tmp_path / "spx.csv", [100.0, 101.0], adjusted=True)
    write_prices(tmp_path / "vix.csv", [15.0, 16.0])
    data = load_market_data("csv", "2024-01-01", spx_csv=tmp_path / "spx.csv", vix_csv=tmp_path / "vix.csv")
    assert data["spx"].iloc[0] == pytest.approx(200.0)


def test_markdown_table_formats_cells():
    frame = pd.DataFrame({"a": [0.1234, float("nan")], "b": [2, 3]}, index=pd.Index(["x", "y"], name="row"))
    lines = markdown_table(frame, {"a": "{:.1%}", "b": "{:.0f}"}).splitlines()
    assert lines[0] == "| row | a | b |"
    assert lines[2] == "| x | 12.3% | 2 |"
    assert lines[3] == "| y |  | 3 |"


def fake_download(calls):
    def download(start):
        calls.append(start)
        dates = pd.bdate_range(start, periods=10)
        return pd.DataFrame({"spx": 4000.0, "vix": 15.0}, index=pd.Index(dates, name="date"))
    return download


def test_cache_keeps_full_history_and_is_reused(tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr("vrp.data.download_yahoo", fake_download(calls))
    cache = tmp_path / "market.csv"
    short = load_market_data("yahoo", "2024-01-01", end="2024-01-05", cache=cache)
    assert len(short) == 5
    assert len(pd.read_csv(cache)) == 10
    full = load_market_data("yahoo", "2024-01-01", cache=cache)
    assert len(full) == 10
    assert calls == ["2024-01-01"]


def test_cache_is_refreshed_when_it_starts_too_late(tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr("vrp.data.download_yahoo", fake_download(calls))
    cache = tmp_path / "market.csv"
    load_market_data("yahoo", "2024-03-01", cache=cache)
    load_market_data("yahoo", "2023-01-02", cache=cache)
    assert calls == ["2024-03-01", "2023-01-02"]


def test_as_percent_scales_and_renames():
    frame = pd.DataFrame({"a": [0.123456, -0.5], "b": [1.0, 2.0]})
    out = as_percent(frame, ["a"], digits=1)
    assert list(out.columns) == ["a (%)", "b"]
    assert out["a (%)"].tolist() == [12.3, -50.0]
    assert frame["a"].iloc[0] == 0.123456
