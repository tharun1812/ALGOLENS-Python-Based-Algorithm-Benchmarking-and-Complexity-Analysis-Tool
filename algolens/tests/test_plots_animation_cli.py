import io

import pytest
from PIL import Image

from algolens import experiment as ex
from algolens import plots
from algolens.animate import make_gif, record_frames
from algolens.cli import main
from algolens.generators import make_input


@pytest.fixture(scope="module")
def records():
    return ex.run_sorting(["bubble", "insertion", "quick_naive", "quick_median3", "timsort", "counting"], trials=1, max_n=256)


def is_png(path):
    with open(path, "rb") as fh:
        return fh.read(8) == b"\x89PNG\r\n\x1a\n"


def test_all_charts_are_written_as_valid_images(records, tmp_path):
    rows = ex.classify_sorting(records)
    files = [plots.plot_growth(records, "random", tmp_path / "g.png"), plots.plot_input_sensitivity(records, tmp_path / "s.png"),
             plots.plot_fingerprint(rows, tmp_path / "f.png"),
             plots.plot_search(ex.run_searching(["binary", "linear"], queries=20, max_n=1024), tmp_path / "q.png")]
    for f in files:
        assert f.stat().st_size > 5000 and is_png(f)
        with Image.open(f) as im:
            assert im.width > 300 and im.height > 200


def test_recorded_animation_frames_start_unsorted_and_end_sorted():
    values = make_input("random", 24, seed=2)
    frames = record_frames("insertion", values, max_frames=30)
    assert frames[0][0] == values and frames[0][2:] == (0, 0)
    assert frames[-1][0] == sorted(values)
    assert len(frames) <= 32
    comparisons = [f[2] for f in frames]
    assert comparisons == sorted(comparisons)                                # counters only go up


def test_algorithms_that_never_write_still_produce_a_frame():
    frames = record_frames("insertion", [1, 2, 3, 4])
    assert frames[0][0] == [1, 2, 3, 4] and frames[-1][0] == [1, 2, 3, 4]


def test_gif_has_many_frames_and_a_hold_at_the_end(tmp_path):
    path = make_gif("bubble", tmp_path / "b.gif", n=12)
    with Image.open(path) as im:
        assert im.format == "GIF" and im.n_frames > 15
    with pytest.raises(ValueError, match="unknown algorithm"):
        make_gif("nope", tmp_path / "x.gif")


def cli(*argv):
    out = io.StringIO()
    code = main(list(argv), out)
    return code, out.getvalue()


def test_cli_list_and_verify():
    code, text = cli("list")
    assert code == 0 and "timsort" in text and "interpolation" in text
    code, text = cli("verify")
    assert code == 0 and "all algorithms verified" in text


def test_cli_analyze_sort_writes_all_outputs(tmp_path):
    code, text = cli("analyze", "sort", "--quick", "--algorithms", "bubble", "merge", "--inputs", "random", "sorted", "--out", str(tmp_path))
    assert code == 0 and "classes with a textbook answer matched" in text
    for name in ("sorting_measurements.csv", "sorting_classification.csv", "sorting_report.md", "growth_random.png", "fingerprint.png",
                 "input_sensitivity.png", "sort_results.json"):
        assert (tmp_path / name).exists(), name
    assert "| bubble | sorted |" in (tmp_path / "sorting_report.md").read_text()


def test_cli_analyze_search_and_animate(tmp_path):
    code, text = cli("analyze", "search", "--quick", "--algorithms", "binary", "jump", "--out", str(tmp_path))
    assert code == 0 and "O(log n)" in text and (tmp_path / "search_growth.png").exists()
    gif = tmp_path / "m.gif"
    code, text = cli("animate", "merge", "--n", "10", "--out", str(gif))
    assert code == 0 and gif.exists()


def test_cli_rejects_bad_arguments(tmp_path):
    with pytest.raises(SystemExit) as exc:
        cli("animate", "not-a-sort")
    assert exc.value.code == 2
    with pytest.raises(SystemExit):
        cli("analyze", "sort", "--inputs", "zigzag")


def test_input_sensitivity_chart_works_for_any_subset_of_algorithms(tmp_path):
    recs = ex.run_sorting(["merge"], ["random", "sorted"], trials=1, max_n=128)         # none of the chart's default algorithms
    assert is_png(plots.plot_input_sensitivity(recs, tmp_path / "one.png"))
