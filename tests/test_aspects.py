import json

import joblib
import pytest

from patchpulse.aspect_model import fit_passage_model, freeze_passage_split, passage_rows
from patchpulse.aspects import analyze_feedback, combine_polarities
from patchpulse.core import ROOT


def polarities(text):
    return {r["aspect"]: r["polarity"] for r in analyze_feedback(text)["aspects"]}


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        (
            "I recommend the game. Great missions, but co-op keeps disconnecting.",
            {"Gameplay": "positive", "Multiplayer": "negative"},
        ),
        ("The combat is fun but the weapons are terrible.", {"Gameplay": "mixed"}),
        ("No crashes this week.", {"Stability": "positive"}),
        ("The performance is not great.", {"Performance": "negative"}),
        ("The server does not work.", {"Multiplayer": "negative"}),
        ("The server no longer disconnects.", {"Multiplayer": "positive"}),
        (
            "The gameplay is fun and multiplayer is broken.",
            {"Gameplay": "positive", "Multiplayer": "negative"},
        ),
        ("The menus are not only good but excellent.", {"Interface": "positive"}),
        ("I recommend the game.", {}),
        ("The server browser lists regions.", {"Multiplayer": "uncertain"}),
        ("Does the game crash?", {"Stability": "uncertain"}),
        ("The crash report is in a folder.", {"Stability": "uncertain"}),
        ("The update fixed crashes.", {"Stability": "positive"}),
        ("The crashes are fixed.", {"Stability": "positive"}),
        ("The crashes are not fixed.", {"Stability": "negative"}),
    ],
)
def test_clause_scope_negation_and_abstention(text, expected):
    assert polarities(text) == expected


def test_evidence_offsets_are_exact_unicode_substrings():
    text = "🚀 Great missions; the servers are broken."
    result = analyze_feedback(text)
    for aspect in result["aspects"]:
        for span in aspect["evidence"]:
            assert text[span["start"] : span["end"]] == span["passage"]
            for cue in span["cues"]:
                assert text[cue["start"] : cue["end"]] == cue["passage"]
    assert not result["input_stored"]


def test_uncertain_does_not_become_neutral_or_absent():
    assert combine_polarities(["uncertain"]) == "uncertain"
    assert combine_polarities(["positive", "negative"]) == "mixed"
    assert combine_polarities(["neutral", "uncertain"]) == "uncertain"


def fixture():
    data = json.loads((ROOT / "data/fixtures/aspect-polarity.json").read_text())
    config = json.loads((ROOT / "configs/aspects.json").read_text(encoding="utf-8-sig"))
    return passage_rows(data["records"]), config


def test_supervised_pipeline_has_no_review_or_author_leakage_and_round_trips(tmp_path):
    rows, config = fixture()
    train, valid, policy = freeze_passage_split(rows, config)
    assert {r["group"] for r in train}.isdisjoint(r["group"] for r in valid)
    assert {r["text"].casefold() for r in train}.isdisjoint(r["text"].casefold() for r in valid)
    model = fit_passage_model(train)
    assert "validationonlysentinel" not in model[:-1].get_feature_names_out()
    joblib.dump(model, tmp_path / "polarity.joblib")
    loaded = joblib.load(tmp_path / "polarity.joblib")
    assert list(model.predict(["Our lobby disconnects every night."])) == list(
        loaded.predict(["Our lobby disconnects every night."])
    )
    assert not any("voted_up" in r for r in train)


def test_duplicate_passages_are_quarantined_and_conflicts_rejected():
    rows, config = fixture()
    duplicate = {**rows[0], "group": "duplicate-author", "version_id": "duplicate-review"}
    _, _, policy = freeze_passage_split(rows + [duplicate], config)
    assert policy["quarantined_duplicate_passages"] == 2
    with pytest.raises(ValueError, match="Conflicting"):
        freeze_passage_split(rows + [{**duplicate, "label": "negative"}], config)


def test_sparse_real_label_support_cannot_silently_train_a_classifier():
    rows, config = fixture()
    with pytest.raises(ValueError, match="Insufficient"):
        freeze_passage_split([r for r in rows if r["label"] == "positive"], config)


def test_synthetic_examples_cannot_bypass_real_human_review_gate():
    from patchpulse.aspect_model import run

    with pytest.raises(ValueError, match="human pilot"):
        run("real")
