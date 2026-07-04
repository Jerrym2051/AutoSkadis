import importlib
import os


def test_fake_mode_and_bins_work(tmp_path, monkeypatch):
    monkeypatch.setenv("FAKE_MODE", "true")
    monkeypatch.setenv("BINS_FILE", str(tmp_path / "bins.json"))

    import config
    import bins

    importlib.reload(config)
    importlib.reload(bins)

    assert config.FAKE_MODE is True

    bins.save_bins({"Test Bin": {"x": 10, "y": 20, "tag_id": 1, "retrieved": False}})
    loaded = bins.load_bins()
    assert loaded["Test Bin"]["x"] == 10

    bins.set_retrieved("Test Bin", True)
    assert bins.is_retrieved("Test Bin") is True
