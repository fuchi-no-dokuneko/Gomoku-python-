# Verification Evidence

## NEKO-68

- Corpus: 21 versioned cases across win, overline, double-three, double-four,
  blocked, positive, negative, symmetry, and edge dimensions.
- Pre-change result: 19 matched and 2 double-four cases mismatched.
- Current result: 21 matched and 0 mismatched.
- Integration: both proven legacy mismatches are rejected by `plane`.

## NEKO-70

- Tests: 57 passed with real game and replay subprocesses.
- Maintained-source coverage: 96 percent across 393 statements.
- Reports: Cobertura XML, JSON, text, complete HTML, and JUnit XML.
- SonarQube Cloud imports `coverage.xml` and `test-results.xml`.
- Policy validator passes exact action pins, read-only permissions, checkout
  credential removal, forbidden-event, fork-token guard, report, and gate checks.

Reproduce locally with the pinned dependencies in `requirements-test.txt`:

```sh
python -m coverage run --parallel-mode -m pytest -q --junitxml=test-results.xml
python -m coverage combine
python -m coverage report --fail-under=95
python tools/check_ci_policy.py
python tools/audit_renju_corpus.py
```
