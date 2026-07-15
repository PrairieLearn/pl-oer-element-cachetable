import importlib
import json
import os
import sys
import types
from pathlib import Path

import pytest

ELEMENT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(ELEMENT_DIR))

sys.modules["chevron"] = types.SimpleNamespace(
    render=lambda _template, params: json.dumps(params)
)

pl_stub = types.SimpleNamespace(
    QuestionData=dict,
    ElementTestData=dict,
    get_string_attrib=lambda element, name, default=None: element.get(name, default),
    get_boolean_attrib=lambda element, name, default=None: (
        element.get(name, str(default)).lower() in {"true", "1", "yes"}
        if element.get(name) is not None
        else default
    ),
    check_attribs=lambda _element, _required, _optional: None,
    check_answers_names=lambda _data, *_names: None,
    get_uuid=lambda: "test-uuid",
)
sys.modules["prairielearn"] = pl_stub

pl_cache_table = importlib.import_module("pl-cache-table")


def _set(tags, blocks, *, valid=None, dirty=None, lru=None):
    valid = list(valid or ["1"] * len(tags))
    dirty = list(dirty or ["0"] * len(tags))
    lru = list(lru or [str(i) for i in range(len(tags))])
    if len(valid) == 1 and len(tags) > 1:
        valid *= len(tags)
    if len(dirty) == 1 and len(tags) > 1:
        dirty *= len(tags)
    if len(lru) == 1 and len(tags) > 1:
        lru *= len(tags)
    result = {
        "tags": list(tags),
        "blocks": [list(block) for block in blocks],
        "valid": valid,
        "dirty": dirty,
        "lru": lru,
    }
    return result


def _cache(
    tags=("0x0",),
    *,
    valid=("1",),
    dirty=("0",),
    blocks=(("0x1", "0x2"),),
    lru=("0",),
):
    return [_set(tags, blocks, valid=valid, dirty=dirty, lru=lru)]


def _base_data() -> dict:
    return {
        "params": {"cache": _cache()},
        "correct_answers": {"cache": _cache()},
        "raw_submitted_answers": {},
        "submitted_answers": {},
        "partial_scores": {},
        "format_errors": {},
        "panel": "question",
    }


def _render(element_html: str, data: dict) -> dict:
    old_cwd = os.getcwd()
    try:
        os.chdir(ELEMENT_DIR)
        return json.loads(pl_cache_table.render(element_html, data))
    finally:
        os.chdir(old_cwd)


def _submit_perfect(data: dict, name: str = "cache") -> None:
    final_cache = data["correct_answers"][name]
    for set_index, cache_set in enumerate(final_cache):
        for way_index, tag in enumerate(cache_set["tags"]):
            data["raw_submitted_answers"][f"{name}_tag{set_index}_{way_index}"] = tag
            data["raw_submitted_answers"][f"{name}_valid{set_index}_{way_index}"] = (
                cache_set["valid"][way_index]
            )
            data["raw_submitted_answers"][f"{name}_dirty{set_index}_{way_index}"] = (
                cache_set["dirty"][way_index]
            )
            data["raw_submitted_answers"][f"{name}_lru{set_index}_{way_index}"] = (
                cache_set["lru"][way_index]
            )
            for offset, value in enumerate(cache_set["blocks"][way_index]):
                data["raw_submitted_answers"][
                    f"{name}_data{set_index}_{way_index}_{offset}"
                ] = value


def test_prepare_accepts_valid_hex_cache_configuration() -> None:
    data = _base_data()

    pl_cache_table.prepare(
        '<pl-cache-table answers-name="cache" set-bits="0" num-ways="1" '
        'block-bits="1" show-valid="true"></pl-cache-table>',
        data,
    )


def test_prepare_rejects_invalid_display_base() -> None:
    with pytest.raises(ValueError, match='base must be "hex" or "bin"'):
        pl_cache_table.prepare(
            '<pl-cache-table answers-name="cache" set-bits="0" num-ways="1" '
            'display-base="dec"></pl-cache-table>',
            _base_data(),
        )


def test_prepare_reports_missing_initial_or_final_cache_configuration() -> None:
    with pytest.raises(ValueError, match="Initial cache configuration"):
        pl_cache_table.prepare(
            '<pl-cache-table answers-name="cache" set-bits="0" num-ways="1" '
            'block-bits="1"></pl-cache-table>',
            {"params": {}, "correct_answers": {"cache": _cache()}},
        )

    with pytest.raises(ValueError, match="Final cache configuration"):
        pl_cache_table.prepare(
            '<pl-cache-table answers-name="cache" set-bits="0" num-ways="1" '
            'block-bits="1"></pl-cache-table>',
            {"params": {"cache": _cache()}, "correct_answers": {}},
        )


def test_prepare_rejects_invalid_tag_characters() -> None:
    data = _base_data()
    data["correct_answers"]["cache"][0]["tags"][0] = "0xz"

    with pytest.raises(ValueError, match="Tag"):
        pl_cache_table.prepare(
            '<pl-cache-table answers-name="cache" set-bits="0" num-ways="1"></pl-cache-table>',
            data,
        )


def test_prepare_rejects_invalid_valid_bit() -> None:
    data = _base_data()
    data["correct_answers"]["cache"][0]["valid"][0] = "2"

    with pytest.raises(ValueError, match="Valid"):
        pl_cache_table.prepare(
            '<pl-cache-table answers-name="cache" set-bits="0" num-ways="1" '
            'show-valid="true"></pl-cache-table>',
            data,
        )


def test_prepare_rejects_invalid_set_and_way_counts() -> None:
    with pytest.raises(ValueError, match="set index"):
        pl_cache_table.prepare(
            '<pl-cache-table answers-name="cache" set-bits="-1" num-ways="1" '
            'block-bits="1"></pl-cache-table>',
            _base_data(),
        )

    with pytest.raises(ValueError, match="ways"):
        pl_cache_table.prepare(
            '<pl-cache-table answers-name="cache" set-bits="0" num-ways="0" '
            'block-bits="1"></pl-cache-table>',
            _base_data(),
        )


def test_prepare_rejects_invalid_data_and_lru_values() -> None:
    data = _base_data()
    data["correct_answers"]["cache"][0]["blocks"][0][1] = "0xz"

    with pytest.raises(ValueError, match="Data"):
        pl_cache_table.prepare(
            '<pl-cache-table answers-name="cache" set-bits="0" num-ways="1" '
            'block-bits="1"></pl-cache-table>',
            data,
        )

    data = _base_data()
    data["correct_answers"]["cache"][0]["blocks"][0][1] = "0XFF"
    pl_cache_table.prepare(
        '<pl-cache-table answers-name="cache" set-bits="0" num-ways="1" '
        'block-bits="1"></pl-cache-table>',
        data,
    )

    data = {
        "params": {
            "cache": _cache(
                ("0x0", "0x1"), blocks=(("1", "2"), ("3", "4")), lru=("0", "1")
            )
        },
        "correct_answers": {
            "cache": _cache(
                ("0x0", "0x1"), blocks=(("1", "2"), ("3", "4")), lru=("z", "1")
            )
        },
    }
    with pytest.raises(ValueError, match="LRU"):
        pl_cache_table.prepare(
            '<pl-cache-table answers-name="cache" set-bits="0" num-ways="2" '
            'block-bits="1"></pl-cache-table>',
            data,
        )


def test_parse_normalizes_hex_fields_and_records_input_errors() -> None:
    data = _base_data()
    data["raw_submitted_answers"] = {
        "cache_tag0_0": " 0X0A ",
        "cache_valid0_0": "2",
        "cache_data0_0_0": "0x1",
        "cache_data0_0_1": "0xZZ",
    }

    pl_cache_table.parse(
        '<pl-cache-table answers-name="cache" set-bits="0" num-ways="1" '
        'block-bits="1" show-valid="true"></pl-cache-table>',
        data,
    )

    assert data["submitted_answers"]["cache_tag0_0"] == "0a"
    assert data["submitted_answers"]["cache_data0_0_0"] == "1"
    assert data["format_errors"] == {
        "cache_valid0_0": "Valid must be 0 or 1.",
        "cache_data0_0_1": 'Data must not have characters besides 0-9, a-f, and "0x".',
    }


def test_parse_missing_nonblank_fields_become_format_errors() -> None:
    data = _base_data()

    pl_cache_table.parse(
        '<pl-cache-table answers-name="cache" set-bits="0" num-ways="1" '
        'block-bits="1" show-valid="true"></pl-cache-table>',
        data,
    )

    assert data["format_errors"]["cache_tag0_0"].startswith("Tag cannot be empty")
    assert data["format_errors"]["cache_valid0_0"].startswith(
        "Valid bit cannot be empty"
    )
    assert data["format_errors"]["cache_data0_0_0"].startswith("Data cannot be empty")


def test_cells_grading_scores_changed_cells_and_penalizes_changed_unchanged_cells() -> (
    None
):
    data = _base_data()
    data["params"]["cache"] = _cache(tags=("0x0",), blocks=(("0x1", "0x2"),))
    data["correct_answers"]["cache"] = _cache(tags=("0xA",), blocks=(("0x1", "0x3"),))
    _submit_perfect(data)
    data["raw_submitted_answers"]["cache_data0_0_0"] = "0x9"

    element_html = (
        '<pl-cache-table answers-name="cache" set-bits="0" num-ways="1" '
        'block-bits="1" grade-mode="cells"></pl-cache-table>'
    )
    pl_cache_table.parse(element_html, data)
    pl_cache_table.grade(element_html, data)

    assert data["partial_scores"]["cache_tag0_0"]["score"] == 1
    assert data["partial_scores"]["cache_data0_0_0"]["score"] == 0
    assert data["partial_scores"]["cache_data0_0_1"]["score"] == 1
    assert data["partial_scores"]["cache"]["score"] == pytest.approx(0.5)


def test_blocks_grading_marks_whole_block_wrong_if_one_cell_is_wrong() -> None:
    data = _base_data()
    data["params"]["cache"] = _cache(tags=("0x0",), blocks=(("0x1", "0x2"),))
    data["correct_answers"]["cache"] = _cache(tags=("0xA",), blocks=(("0x1", "0x3"),))
    _submit_perfect(data)
    data["raw_submitted_answers"]["cache_data0_0_1"] = "0x4"

    element_html = (
        '<pl-cache-table answers-name="cache" set-bits="0" num-ways="1" '
        'block-bits="1" grade-mode="blocks"></pl-cache-table>'
    )
    pl_cache_table.parse(element_html, data)
    pl_cache_table.grade(element_html, data)

    assert data["partial_scores"]["cache_block0_0"]["score"] == 0
    assert data["partial_scores"]["cache"]["score"] == 0


def test_all_or_nothing_requires_all_cells_correct() -> None:
    data = _base_data()
    data["correct_answers"]["cache"] = _cache(tags=("0xA",), blocks=(("0x1", "0x3"),))
    _submit_perfect(data)
    data["raw_submitted_answers"]["cache_tag0_0"] = "0xb"

    element_html = (
        '<pl-cache-table answers-name="cache" set-bits="0" num-ways="1" '
        'block-bits="1" grade-mode="all-or-nothing"></pl-cache-table>'
    )
    pl_cache_table.parse(element_html, data)
    pl_cache_table.grade(element_html, data)

    assert data["partial_scores"]["cache"]["score"] == 0


def test_render_exposes_fully_associative_metadata_and_cell_feedback() -> None:
    data = _base_data()
    data["params"]["cache"] = _cache(
        tags=("0x0", "0x1"), blocks=(("0x1", "0x2"), ("0x3", "0x4")), lru=("0", "1")
    )
    data["correct_answers"]["cache"] = _cache(
        tags=("0x0", "0x2"), blocks=(("0x1", "0x2"), ("0x3", "0x5")), lru=("1", "0")
    )
    _submit_perfect(data)
    element_html = (
        '<pl-cache-table answers-name="cache" set-bits="0" num-ways="2" '
        'block-bits="1" show-valid="true" show-dirty="true" '
        'grade-mode="cells"></pl-cache-table>'
    )
    pl_cache_table.parse(element_html, data)
    pl_cache_table.grade(element_html, data)
    rendered = _render(element_html, data)

    assert rendered["question"] is True
    assert rendered["fully_assoc"] is True
    assert rendered["has_lru"] is True
    assert rendered["way_display_width"] == 5
    assert rendered["cache_sets"][0]["ways"][1]["tag_correct"] is True
    assert rendered["cache_sets"][0]["lru"][0]["lru_correct"] is True


def test_render_read_only_displays_material_and_accepts_legacy_alias() -> None:
    data = _base_data()
    element_html = (
        '<pl-cache-table answers-name="cache" set-bits="0" num-ways="1" '
        'block-bits="1" read-only="true"></pl-cache-table>'
    )

    pl_cache_table.prepare(element_html, data)
    rendered = _render(element_html, data)

    assert rendered["is_material"] is True

    legacy_data = _base_data()
    legacy_html = (
        '<pl-cache-table answers-name="cache" set-bits="0" num-ways="1" '
        'block-bits="1" is-material="true"></pl-cache-table>'
    )
    pl_cache_table.prepare(legacy_html, legacy_data)
    legacy_rendered = _render(legacy_html, legacy_data)

    assert legacy_rendered["is_material"] is True
