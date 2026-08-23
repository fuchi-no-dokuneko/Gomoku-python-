# Renju Rule Variant and Corpus

## Scope

The corpus applies the Renju International Federation (RIF) 1996 rules with the
1998 correction to this project's legacy 19x19 board. It covers line outcomes
after a candidate move. Tournament procedure, clocks, claims, passes, and opening
protocols are outside this engine's scope.

RIF defines five, overline, four, straight four, three, double-four, and
double-three in sections 3 and 9. Black wins with exact five. Without attaining
five simultaneously, black loses on overline, double-four, or a forbidden
double-three. White wins with five or more.

Primary source: [RIF International Rules of Renju](https://www.renju.net/rifrules/),
decided 2 May 1996 and corrected 3 May 1998.

## Corpus Contract

`renju/corpus.json` is versioned data. Each case contains the candidate move,
existing black and white stones, rule family, coverage kind, and complete expected
outcome. Coordinates are zero-based `[row, column]`. `positive`, `negative`,
`symmetry`, and `edge` cases are mandatory for every supported rule family.

`blocked` cases prove that board edges and opposing stones terminate rows and
prevent a closed arm from being counted as an open three or usable four. The
corpus intentionally includes white overline to prove the color asymmetry.

## Audit Order

Run `python tools/audit_renju_corpus.py --report docs/initial-renju-mismatches.md`
against the untouched legacy implementation. Retain that generated report before
changing behavior. The conformance test then runs the same immutable corpus
against the replacement evaluator.
