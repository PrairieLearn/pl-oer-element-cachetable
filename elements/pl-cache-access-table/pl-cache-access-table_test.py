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

pl_cache_access = importlib.import_module("pl-cache-access-table")


def _base_data() -> dict:
    return {
        "correct_answers": {
            "access": [
                {"address": "0x1a", "hit": False},
                {"address": "0x1f", "hit": True},
                {"address": "0x20", "hit": False},
            ]
        },
        "raw_submitted_answers": {},
        "submitted_answers": {},
        "partial_scores": {},
        "format_errors": {},
        "feedback": {},
        "panel": "question",
    }


def _render(element_html: str, data: dict) -> dict:
    old_cwd = os.getcwd()
    try:
        os.chdir(ELEMENT_DIR)
        return json.loads(pl_cache_access.render(element_html, data))
    finally:
        os.chdir(old_cwd)


def test_prepare_requires_string_addresses_and_boolean_hit_values() -> None:
    data = _base_data()
    data["correct_answers"]["access"][0]["address"] = 10

    with pytest.raises(AttributeError, match="Addresses need to be a string"):
        pl_cache_access.prepare(
            '<pl-cache-access-table answers-name="access"></pl-cache-access-table>',
            data,
        )


def test_prepare_reports_missing_access_sequence() -> None:
    with pytest.raises(ValueError, match="Sequence of cache accesses"):
        pl_cache_access.prepare(
            '<pl-cache-access-table answers-name="access"></pl-cache-access-table>',
            {"correct_answers": {}},
        )


def test_prepare_requires_boolean_hit_values() -> None:
    data = _base_data()
    data["correct_answers"]["access"][0]["hit"] = "Miss"

    with pytest.raises(AttributeError, match="Hit need to be a Boolean"):
        pl_cache_access.prepare(
            '<pl-cache-access-table answers-name="access"></pl-cache-access-table>',
            data,
        )


def test_parse_marks_missing_hit_miss_choices_as_format_errors() -> None:
    data = _base_data()

    pl_cache_access.parse(
        '<pl-cache-access-table answers-name="access"></pl-cache-access-table>',
        data,
    )

    assert data["format_errors"] == {
        "access0_hit": "Must select a hit or miss",
        "access1_hit": "Must select a hit or miss",
        "access2_hit": "Must select a hit or miss",
    }


def test_empty_cache_auto_submits_first_access_as_miss() -> None:
    data = _base_data()

    pl_cache_access.parse(
        '<pl-cache-access-table answers-name="access" empty-cache="true"></pl-cache-access-table>',
        data,
    )

    assert data["submitted_answers"]["access0_hit"] == "Miss"
    assert "access0_hit" not in data["format_errors"]


def test_parse_keeps_submitted_choices_without_format_errors() -> None:
    data = _base_data()
    data["raw_submitted_answers"] = {
        "access0_hit": "Miss",
        "access1_hit": "Hit",
        "access2_hit": "Miss",
    }

    pl_cache_access.parse(
        '<pl-cache-access-table answers-name="access"></pl-cache-access-table>',
        data,
    )

    assert data["format_errors"] == {}


def test_through_first_grading_stops_at_first_error() -> None:
    data = _base_data()
    data["raw_submitted_answers"] = {
        "access0_hit": "Miss",
        "access1_hit": "Miss",
        "access2_hit": "Miss",
    }

    pl_cache_access.grade(
        '<pl-cache-access-table answers-name="access"></pl-cache-access-table>',
        data,
    )

    assert data["partial_scores"]["access"]["score"] == pytest.approx(1 / 3)
    assert data["feedback"]["access"] == "Your first error was on access number 1."
    assert "access2_hit" not in data["partial_scores"]


def test_all_grading_scores_every_access_independently() -> None:
    data = _base_data()
    data["raw_submitted_answers"] = {
        "access0_hit": "Miss",
        "access1_hit": "Miss",
        "access2_hit": "Hit",
    }

    pl_cache_access.grade(
        '<pl-cache-access-table answers-name="access" grade-mode="all"></pl-cache-access-table>',
        data,
    )

    assert data["partial_scores"]["access0_hit"]["score"] == 1
    assert data["partial_scores"]["access1_hit"]["score"] == 0
    assert data["partial_scores"]["access2_hit"]["score"] == 0
    assert data["partial_scores"]["access"]["score"] == pytest.approx(1 / 3)


def test_all_or_nothing_grading_zeroes_partial_success() -> None:
    data = _base_data()
    data["raw_submitted_answers"] = {
        "access0_hit": "Miss",
        "access1_hit": "Miss",
        "access2_hit": "Miss",
    }

    pl_cache_access.grade(
        '<pl-cache-access-table answers-name="access" grade-mode="all-or-nothing"></pl-cache-access-table>',
        data,
    )

    assert data["partial_scores"]["access"]["score"] == 0


def test_empty_cache_grading_ignores_first_auto_miss() -> None:
    data = _base_data()
    data["raw_submitted_answers"] = {
        "access1_hit": "Hit",
        "access2_hit": "Miss",
    }

    pl_cache_access.grade(
        '<pl-cache-access-table answers-name="access" empty-cache="true"></pl-cache-access-table>',
        data,
    )

    assert "access0_hit" not in data["partial_scores"]
    assert data["partial_scores"]["access"]["score"] == 1


def test_render_question_includes_grade_info_and_first_miss_marker() -> None:
    data = _base_data()
    data["raw_submitted_answers"] = {"access0_hit": "Miss", "access1_hit": "Hit"}
    data["partial_scores"]["access"] = {"score": 2 / 3, "weight": 1}
    data["partial_scores"]["access0_hit"] = {"score": 1, "weight": 0}
    data["partial_scores"]["access1_hit"] = {"score": 1, "weight": 0}
    data["partial_scores"]["access2_hit"] = {"score": 0, "weight": 0}

    rendered = _render(
        '<pl-cache-access-table answers-name="access" empty-cache="true" '
        'show-partial-score="false" show-percentage-score="false"></pl-cache-access-table>',
        data,
    )

    assert rendered["question"] is True
    assert rendered["score"] == 66.67
    assert rendered["all_partial"] is True
    assert rendered["accesses"][0]["first_miss"] is True
    assert rendered["accesses"][0]["correct"] is False
    assert "Partial score information will not be shown" in rendered["grade-info"]
    assert "Total percentage score" in rendered["grade-info"]


def test_render_rejects_unknown_grade_mode() -> None:
    with pytest.raises(AttributeError, match="grade-mode"):
        _render(
            '<pl-cache-access-table answers-name="access" grade-mode="mystery"></pl-cache-access-table>',
            _base_data(),
        )


def test_render_submission_marks_correct_and_incorrect_choices() -> None:
    data = _base_data()
    data["panel"] = "submission"
    data["raw_submitted_answers"] = {
        "access0_hit": "Miss",
        "access1_hit": "Miss",
        "access2_hit": "Miss",
    }

    pl_cache_access.grade(
        '<pl-cache-access-table answers-name="access" grade-mode="all"></pl-cache-access-table>',
        data,
    )
    rendered = _render(
        '<pl-cache-access-table answers-name="access" grade-mode="all"></pl-cache-access-table>',
        data,
    )

    assert rendered["submission"] is True
    assert rendered["accesses"][0]["correct"] is True
    assert rendered["accesses"][1]["incorrect"] is True
    assert rendered["accesses"][0]["sub_text"] == "Miss"
