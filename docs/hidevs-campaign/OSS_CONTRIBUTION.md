# OSS Contribution Candidate

**Prepared:** 2026-10-12  
**Status:** Implemented and tested locally; **not submitted, not assigned, not merged**

## Candidate

- Upstream: [modelcontextprotocol/python-sdk](https://github.com/modelcontextprotocol/python-sdk)
- Issue: [#3692 — Tool handlers returning `UserList` lose native content blocks despite `Sequence` return annotation](https://github.com/modelcontextprotocol/python-sdk/issues/3692)
- Local base commit: [`c9356a2a8fb805ac2202e44c05371cf005edc923`](https://github.com/modelcontextprotocol/python-sdk/commit/c9356a2a8fb805ac2202e44c05371cf005edc923)
- Local branch: `oss/3692-userlist-tool-content`
- Local patch commit: `a890ba2` (`fix(mcpserver): preserve content from non-list sequences`)
- Local checkout: `C:\Users\User\mcp-python-sdk-oss`

This candidate is distinct from the SentinelOps competition code. It fixes a reproducible SDK behavior in an established upstream project rather than adding competition-specific functionality to Janice's repository.

## Problem reproduced

The SDK recognizes `Sequence[ContentBlock]` as a content-bearing return annotation, but runtime conversion previously flattened only concrete `list` and `tuple` values. A tool returning `collections.UserList` under a `Sequence[TextContent]` annotation therefore produced one serialized textual value instead of the native content blocks implied by the annotation.

Before the source change, the two new public client/server regression tests failed while the scalar text/binary guard tests passed. This supplies red/green evidence for the reported defect and guards against broadening conversion to string-like sequences.

## Local implementation

Changed files in the upstream checkout:

- `src/mcp/server/mcpserver/utilities/func_metadata.py`
  - Flatten any runtime `collections.abc.Sequence` into content blocks.
  - Explicitly retain `str`, `bytes`, `bytearray`, and `memoryview` on their prior single-block serialization paths.
  - Align comments and public function documentation with the existing `Sequence[...]` annotation behavior.
- `tests/server/mcpserver/test_server.py`
  - Add in-memory client/server tests for populated and empty `UserList` results.
- `tests/server/mcpserver/test_func_metadata.py`
  - Add regression coverage for text and binary sequence-like values, including `memoryview`.

## Verification evidence

| Check | Result |
|---|---|
| New tests before source fix | 2 expected failures for `UserList`; scalar/binary guards passed |
| Focused final regressions | **6 passed** |
| Clean full run before the final `memoryview` guard test was added | **6,202 passed, 16 skipped, 1 xfailed** |
| Full run after the guard test | 6,201 passed; 2 unrelated HTTP/client timeout failures; 16 skipped; 1 xfailed |
| Full retry after the guard test | 6,202 passed; 1 unrelated server-runner timeout failure; 16 skipped; 1 xfailed |
| Isolated stress reruns of the three unrelated failures | **15 passed** (5 repetitions per test) |
| Coverage from the clean full run | **100.00%** across 54,163 statements and 4,250 branches |
| Ruff format check | Passed across 870 files |
| Ruff lint | Passed |
| Pyright on all three changed files | 0 errors, 0 warnings |
| `git diff --check` | Passed |
| New suppression directives | None |

### Environment-specific verification limitations

- The repository's POSIX `scripts/test` entry point could not execute directly because this Windows host has no compatible `/bin/sh`/WSL runtime. Its commands were run individually in PowerShell instead.
- Repository-wide Pyright reports 34 pre-existing platform/stub errors in POSIX/Win32 process code and unrelated stdio tests. The three changed files pass Pyright cleanly.
- `strict-no-cover` 0.1.1 uses an open `NamedTemporaryFile` that its child process cannot reopen on Windows. With a Windows-compatible temporary-file wrapper, it runs and reports 80 pre-existing Windows stdio lines whose `pragma: no cover` markers are exercised on this platform. The patch adds no coverage suppressions and its full suite still reports 100.00% coverage.
- Two final full-suite attempts encountered three unrelated five-second timing failures in HTTP/client/server tests outside the changed files. All three tests passed five consecutive isolated reruns. They are reported as environmental flakes rather than hidden or counted as clean full-suite passes.

## Upstream policy gate

The upstream [contribution policy](https://github.com/modelcontextprotocol/python-sdk/blob/main/CONTRIBUTING.md) requires an issue to be assigned before a pull request is opened. Issue #3692 currently has no assignee, and the reporter has already expressed interest in contributing the fix. The responsible next step is therefore to coordinate on the issue and obtain maintainer assignment before pushing or opening a pull request.

No issue comment, fork, push, or pull request has been created. Those are external actions and require Janice's approval. Even after approval, this work must remain described as **prepared** until submitted and **submitted** until an upstream maintainer actually merges it.

## Draft upstream communication

> I reproduced this on current `main` and prepared a focused local fix with public client/server regression coverage for populated and empty `UserList` results, plus guards for string and binary sequence-like values. A clean full Windows run completed with 6,202 passed, 16 skipped, 1 xfailed and 100% coverage. After adding one final `memoryview` guard test, two full retries hit unrelated five-second transport/server timeouts; each failed test then passed 5/5 isolated. The changed files pass Ruff and Pyright. I see that the reporter has offered to contribute, so I do not want to pre-empt them. If maintainers and the reporter prefer, I can share the patch or take an assignment under the contribution policy. AI assistance was used during implementation and verification.

## Draft pull request

**Title:** `fix(mcpserver): preserve content blocks from non-list sequences`

**Summary:**

- make runtime content conversion match `Sequence[...]` return annotations;
- preserve native blocks returned through `UserList` and other non-string sequences;
- keep text and binary sequence-like values on their existing serialization path;
- add in-memory server regressions and scalar/binary guards.

**Validation:**

- clean full run: `6202 passed, 16 skipped, 1 xfailed` and 100.00% coverage;
- final focused regressions: `6 passed`;
- three unrelated full-retry timeout failures: each passed 5/5 isolated;
- Ruff format/lint passed;
- changed-file Pyright passed.

**Disclosure:** AI assistance was used to analyze the issue, implement the patch, and prepare tests; all changes and results were locally reviewed and executed.

`Fixes #3692`
