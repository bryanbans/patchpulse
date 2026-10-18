# Third-party content

Steam and the named games belong to their respective owners. PatchPulse is independent and does not imply endorsement. No game artwork or logos are included. The DRG tile is original plain text.

The public fixtures contain original synthetic sentences, invented recommendation labels, and invented timestamps. They are not copied or paraphrased Steam reviews. Screenshots show synthetic mode only.

Steam review text, private pseudonymous author groups, collection caches, and fitted models are excluded from Git. API availability does not establish a right to redistribute data or trained artifacts. See [source audit](docs/data_sources.md). Third-party software retains its own licenses; exact resolved versions appear in uv.lock and web/package-lock.json. No transformer weights are distributed.


The optional neural experiment uses the pinned `distilbert/distilbert-base-uncased` base model, whose [model card](https://huggingface.co/distilbert/distilbert-base-uncased/tree/12040accade4e8a0f71eabdb258fecc2e7e948be) declares Apache-2.0. Pretrained and fine-tuned weights/tokenizers remain private and are not included in this repository. This license does not grant rights to the Steam training text or settle fitted-artifact distribution. Hugging Face Transformers and PyTorch are optional separately licensed dependencies; exact artifacts are locked in uv.lock.
