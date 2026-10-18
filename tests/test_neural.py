import pytest

from patchpulse.neural import class_weights, select_common_checkpoint


def test_loss_weights_use_training_class_support():
    assert class_weights([0, 1, 1, 1]) == [2, 2 / 3]
    with pytest.raises(ValueError, match="Both training"):
        class_weights([1, 1])


def test_common_epoch_selection_never_chooses_best_seed():
    config = {"candidates": [{"id": "a"}, {"id": "b"}], "seeds": [17, 42, 73], "epochs": 2}
    rows = []
    for candidate in ["a", "b"]:
        for epoch in [1, 2]:
            for seed in config["seeds"]:
                value = 0.6 if candidate == "a" else (0.99 if seed == 17 else 0.3)
                rows.append(
                    {"id": candidate, "seed": seed, "epoch": epoch, "macro_f1": value, "negative_f1": value}
                )
    selection, _ = select_common_checkpoint(rows, config)
    assert selection["id"] == "a"
    assert selection["epoch"] == 1
    assert selection["mean_macro_f1"] == pytest.approx(0.6)
    with pytest.raises(ValueError, match="Incomplete"):
        select_common_checkpoint(rows[:-1], config)
    with pytest.raises(ValueError, match="duplicate"):
        select_common_checkpoint(rows + [rows[0]], config)


def test_neural_encoder_and_head_receive_gradients_without_model_download():
    """Optional offline neural smoke; standard demo CI does not install PyTorch."""
    torch = pytest.importorskip("torch")
    transformers = pytest.importorskip("transformers")
    torch.manual_seed(42)
    config = transformers.DistilBertConfig(
        vocab_size=40,
        dim=16,
        hidden_dim=32,
        n_layers=1,
        n_heads=2,
        max_position_embeddings=16,
        dropout=0,
        attention_dropout=0,
        seq_classif_dropout=0,
        num_labels=2,
    )
    model = transformers.DistilBertForSequenceClassification(config)
    before = model.distilbert.embeddings.word_embeddings.weight.detach().clone()
    batch = {
        "input_ids": torch.tensor([[1, 2, 3], [1, 4, 5]]),
        "attention_mask": torch.ones((2, 3), dtype=torch.long),
    }
    optimizer = torch.optim.AdamW(model.parameters(), lr=0.01)
    loss = torch.nn.functional.cross_entropy(model(**batch).logits, torch.tensor([0, 1]))
    loss.backward()
    assert model.classifier.weight.grad.abs().sum() > 0
    assert model.distilbert.embeddings.word_embeddings.weight.grad.abs().sum() > 0
    optimizer.step()
    assert not torch.equal(before, model.distilbert.embeddings.word_embeddings.weight)
