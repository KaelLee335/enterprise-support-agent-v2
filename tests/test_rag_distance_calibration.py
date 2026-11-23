from scripts.calibrate_rag_distance import PROBES, _stats


def test_distance_stats_interpolate_quartiles() -> None:
    assert _stats([4.0, 1.0, 3.0, 2.0]) == {
        "min": 1.0,
        "p25": 1.75,
        "median": 2.5,
        "p75": 3.25,
        "max": 4.0,
    }


def test_empty_distance_stats_are_explicit() -> None:
    assert _stats([]) == {
        "min": None,
        "p25": None,
        "median": None,
        "p75": None,
        "max": None,
    }


def test_calibration_probes_are_separate_and_well_labeled() -> None:
    ids = [probe["id"] for probe in PROBES]
    assert len(ids) == 24
    assert len(set(ids)) == len(ids)
    assert sum(probe["kind"] == "answerable" for probe in PROBES) == 12
    assert sum(probe["kind"] == "unsupported" for probe in PROBES) == 12
    assert all(probe["target"] for probe in PROBES if probe["kind"] == "answerable")
    assert all(probe["target"] is None for probe in PROBES if probe["kind"] == "unsupported")
