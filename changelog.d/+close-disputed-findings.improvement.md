When a person says one of marginal's inline findings is wrong, marginal now
closes it and credits them: it replies `✅ Resolved: @alice says this isn't an
issue ("…"), so marginal is closing it.` and resolves the thread. The person
can answer in the finding's own thread or in an ordinary PR comment; the
model matches each open finding against the human replies in its thread and
the human PR comments posted after it, so an unrelated comment such as "LGTM"
or a question closes nothing, and a dismissal only counts if it names one of
those comments. This runs wherever marginal re-checks open findings: in
`marginal compact` and on every later `marginal review --comment`

([PR-128](https://github.com/exactml/marginal/pull/128) by [@exactml](https://github.com/exactml))
