A marginal review now opens with its verdict, so the outcome is readable
without opening any inline thread: `**3 findings** · 🔴 1 critical · 🟠 2
high`, counted by severity with the most serious first, or `✅ **No issues
found**` when the model reviewed the diff and flagged nothing. On a re-run it
counts only what's new and notes how many were already flagged earlier on
the PR. A run without a reviewer model shows no verdict, so it never claims
"no issues" for a diff nobody reviewed. The base and head SHAs in the header
are shortened to 7 characters

([PR-XX](https://github.com/exactml/marginal/pull/XX) by [@exactml](https://github.com/exactml))
