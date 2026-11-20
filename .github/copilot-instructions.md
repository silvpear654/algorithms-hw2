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
- 코드를 쓰기 전에 SPEC.md를 읽는다.
- src/ 안에서 dict, set, 내장 hash()를 쓰지 않는다. 해시 테이블은 직접 만든 것을 쓴다.
- 코드를 고친 뒤에는 make test를 돌리고 결과를 보여 준다.
- 테스트가 실패하면 테스트가 아니라 코드를 고친다.
- 이슈마다 develop에서 feature/<이슈번호>-<이름> 브랜치를 따서 작업하고, 진행은 이슈 댓글로 남긴다.
- 끝나면 커밋하고 develop에 머지한 뒤 push하고, 이슈를 닫는다.
- 나는 1학년이다. 무엇을 바꿨는지 세 줄 이내로 요약한다.

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
