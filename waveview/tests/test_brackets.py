from waveview.brackets import BracketSpec, compute_brackets


def test_empty():
    assert compute_brackets([]) == ([], [])


def test_no_shared_prefix():
    spans, consumed = compute_brackets(["a", "b", "c"])
    assert spans == []
    assert consumed == [0, 0, 0]


def test_single_top_prefix():
    spans, consumed = compute_brackets(["dut.a", "dut.b", "dut.c"])
    assert spans == [BracketSpec("dut", 0, 0, 3)]
    assert consumed == [1, 1, 1]


def test_lone_row_keeps_qualifier():
    # row 2 stands alone — no bracket for it; its qualifier survives in label.
    spans, consumed = compute_brackets(["dut.foo.a", "dut.foo.b", "dut.bar.c"])
    assert BracketSpec("dut", 0, 0, 3) in spans
    assert BracketSpec("foo", 1, 0, 2) in spans
    # bar has only one row → no bracket
    assert all(s.name != "bar" for s in spans)
    assert consumed == [2, 2, 1]  # rows 0/1 inside foo; row 2 only inside dut


def test_single_child_chain_merges():
    paths = [
        "top.inner.scope.x",
        "top.inner.scope.y",
        "top.inner.scope.z",
    ]
    spans, consumed = compute_brackets(paths)
    # All three components collapse into one bracket name, single lane.
    assert spans == [BracketSpec("top.inner.scope", 0, 0, 3)]
    assert consumed == [3, 3, 3]


def test_siblings_break_merge():
    paths = [
        "dut.cell(0).i.clk",
        "dut.cell(0).i.rst",
        "dut.cell(1).i.clk",
        "dut.cell(1).i.rst",
    ]
    spans, consumed = compute_brackets(paths)
    # Outer "dut" wraps everything; then two sibling cell brackets, each
    # merged with the trailing single-child ".i" segment.
    assert BracketSpec("dut", 0, 0, 4) in spans
    assert BracketSpec("cell(0).i", 1, 0, 2) in spans
    assert BracketSpec("cell(1).i", 1, 2, 4) in spans
    assert consumed == [3, 3, 3, 3]


def test_mixed_depths():
    paths = [
        "dut.srnddata",
        "dut.srndvalid",
        "dut.neotrng.clk",
        "dut.neotrng.enable",
    ]
    spans, consumed = compute_brackets(paths)
    assert BracketSpec("dut", 0, 0, 4) in spans
    assert BracketSpec("neotrng", 1, 2, 4) in spans
    # Lone scalars under dut keep their leaf only (consumed=1).
    assert consumed == [1, 1, 2, 2]


def test_disjoint_top_level():
    paths = ["alpha.a", "alpha.b", "beta.x", "beta.y"]
    spans, consumed = compute_brackets(paths)
    assert BracketSpec("alpha", 0, 0, 2) in spans
    assert BracketSpec("beta", 0, 2, 4) in spans
    assert consumed == [1, 1, 1, 1]
