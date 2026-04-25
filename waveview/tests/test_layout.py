from waveview.layout import format_time, pick_axis_unit, pick_tick_step


def test_pick_axis_unit_50ns_step_in_fs_dump():
    # step = 50 ns expressed in fs (10^-15)
    exp, prefix = pick_axis_unit(50_000_000, -15)
    assert (exp, prefix) == (-9, "n")


def test_pick_axis_unit_5ms_step_in_fs_dump():
    # step = 5 ms = 5e12 fs
    exp, prefix = pick_axis_unit(5_000_000_000_000, -15)
    assert (exp, prefix) == (-3, "m")


def test_pick_axis_unit_5ps_step_in_fs_dump():
    exp, prefix = pick_axis_unit(5_000, -15)
    assert (exp, prefix) == (-12, "p")


def test_pick_axis_unit_uneven_step_falls_back():
    # 7 fs is not divisible by any larger SI unit
    exp, prefix = pick_axis_unit(7, -15)
    assert (exp, prefix) == (-15, "f")


def test_format_time_zero_no_unit():
    assert format_time(0, -15, -9, "n") == "0"


def test_format_time_clean_ns_in_fs_dump():
    # 250000000 fs = 250 ns
    assert format_time(250_000_000, -15, -9, "n") == "250ns"


def test_format_time_clean_ms_in_fs_dump():
    assert format_time(2_000_000_000_000, -15, -3, "m") == "2ms"


def test_format_time_negative():
    assert format_time(-50_000_000, -15, -9, "n") == "-50ns"


def test_format_time_no_scientific_notation():
    # Regression: 250000000 fs used to render as "2.5e+08fs" because float
    # division didn't round-trip to int. Now must produce a clean SI label.
    label = format_time(250_000_000, -15, -9, "n")
    assert "e+" not in label and "e-" not in label


def test_pick_tick_step_round_numbers():
    # Spans should snap to 1, 2, 5 * 10^k.
    assert pick_tick_step(0, 100) in (10, 20, 50)
    assert pick_tick_step(0, 650_000_000) == 50_000_000
