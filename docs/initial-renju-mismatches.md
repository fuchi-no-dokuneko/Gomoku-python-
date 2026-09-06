# Initial Renju Corpus Audit

This report captures the pre-change legacy behavior. It is generated before
the rule implementation is changed and is retained as mismatch evidence.

Variant: `RIF-1998-line-rules-on-legacy-19x19`
Cases: 21; matched: 19; mismatched: 2

| Case | Rule | Kind | Expected | Legacy result |
| --- | --- | --- | --- | --- |
| double-four-positive-cross | double_four | positive | double_four (legal=False, win=False) | legal (legal=True, win=False) |
| double-four-symmetry-diagonals | double_four | symmetry | double_four (legal=False, win=False) | legal (legal=True, win=False) |
