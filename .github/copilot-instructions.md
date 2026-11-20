# Copilot instructions

## Project constraints

- Read `SPEC.md` and the relevant tests before changing implementation.
- Use only the Python standard library.
- In `src/`, do not use `dict`, `set`, or Python's built-in `hash()`. Use the
  hand-written hash tables and the polynomial Horner hash in
  `src/hash_table.py`.
- Short codes must come from the base62 counter, never from a hash value.
- Add or update focused tests before implementing new behavior. Do not weaken
  tests to make an implementation pass.
- Keep table capacities fixed and preserve probe counts and inspection data.
- Validate inputs explicitly and report errors using the behavior in `SPEC.md`.

## Git workflow

- Start from `develop` and create `feature/<issue-number>-<short-name>` for
  each issue.
- Post progress updates to the matching GitHub issue while working.
- Commit each completed step with subject
  `Step N: 한 일 (#이슈번호)`.
- Push the feature commit, merge the feature into `develop`, then push
  `develop`. Close an issue only after its work is complete.
- Do not commit unrelated changes or rewrite existing commits.

## Validation

- Run `make test` after behavior changes.
- Before finishing, scan `src/` for forbidden built-ins and inspect the
  resulting diff and worktree status.
