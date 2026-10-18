`marginal review` now also reads maintainers' answers to findings it posted
in the review body (findings with no line), so the next review doesn't raise
an already-answered point again. GitHub doesn't allow replies on a review
body, so a PR comment from a person, posted after marginal's review, counts
as an answer to that review's body findings.

([PR-128](https://github.com/exactml/marginal/pull/128) by [@exactml](https://github.com/exactml))
