# eval

`scorer.py` turns a set of envelopes with labels into a score sheet (rates with Wilson 95 % intervals).
It needs no model: `python eval/scorer.py items.jsonl`, one `{"id", "expect", "envelope"}` object per line.

Evaluation items are not kept in this repository, and are never mixed into training data.
