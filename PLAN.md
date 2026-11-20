# Implementation plan

## Scope and corrections

Implement the behavior in `SPEC.md`, not a generic URL-shortener design.
In particular, do not use `dict`, `set`, or built-in `hash()` in `src/`, do not
derive codes from hashes, and write core behavior tests before implementing it.
Keep table capacities fixed so the experiments can control load factor.

## Sequence

1. Provide and test the base62 conversion independently.
2. Write focused tests for the hash-table and shortener boundary cases before
   adding those implementations. Keep tests unchanged while making them pass.
3. Implement a shared Horner-hash calculation and separate-chaining table, then
   linear probing with identical public operations and explicit full-table
   handling.
4. Implement URL validation, idempotent URL mapping, counter-based base62
   codes, and expansion using the chaining table.
5. Add source-level project rules and verify the implementation follows them.
6. Measure chained-table probe counts across controlled load factors and
   compare observed values with the theoretical successful and unsuccessful
   search estimates.
7. Add the standard-library HTTP form, shortening response, redirect, and table
   inspection view; validate routes locally.
8. Compare chaining and linear probing on identical keys and capacities,
   including wraparound and a full table. Produce the requested graph and a
   report of at most two pages.

## Validation

- Run `make test` after each behavior change.
- Include collision, overwrite, deletion, missing-key, zero, invalid input,
  wraparound, and full-table cases in focused tests.
- Check every `src/` file for forbidden built-ins.
- Run experiments from a fresh process and verify reported probe metrics
  against the table implementations' operation counters.
- Exercise HTTP success, invalid input, redirects, table inspection, and 404
  behavior without depending on public port forwarding.
