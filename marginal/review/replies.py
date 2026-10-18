"""Find maintainer replies to marginal's own inline comments on a PR.

When a maintainer answers one of marginal's findings ("intentional, here's
why"), the next run on the same PR otherwise has no memory of it and tends to
raise the same point again in new words. GitHub's review-comment threads are
already the durable store for that answer, so this reads them back.

A finding with no line is posted in the review body instead, which GitHub
gives no reply thread; maintainers answer those in an ordinary PR comment,
so `body_finding_replies` reads those back too.
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass

from marginal.review.dedup import _MARKER

# The severity+confidence badge every marginal finding opens with. Releases
# before the fingerprint marker existed posted findings with only this, so
# it's the one way to recognize those older comments as marginal's own.
_BADGE = re.compile(r"^(?:🔴|🟠|🟡|⚪) \*\*(?:Critical|High|Medium|Low)\*\* · \d+% confidence")
# A review-body finding's badge also names its file: "... confidence — `path`".
_BODY_BADGE = re.compile(_BADGE.pattern + r" — `([^`\n]+)`$", re.MULTILINE)


@dataclass(frozen=True)
class ReplyThread:
    """One of marginal's inline comments and the maintainer replies to it."""

    path: str
    line: int | None
    comment: str
    replies: tuple[str, ...]


# Ends every reply `marginal compact` posts to close a stale finding.
RESOLVED_MARKER = "<!-- marginal:resolved -->"


def is_marginal_comment(body: str | None) -> bool:
    """Whether `body` was posted by marginal: a finding (fingerprint marker or
    severity badge) or a `marginal compact` resolution reply."""
    return bool(body) and bool(
        _MARKER.search(body) or _BADGE.match(body) or RESOLVED_MARKER in body
    )


def maintainer_replies(comments: Iterable[dict[str, object]]) -> list[ReplyThread]:
    """Threads under marginal's inline comments that a person replied to.

    `comments` is GitHub's list of a PR's review comments, oldest first; a
    reply's `in_reply_to_id` always names its thread's first comment. Replies
    under anyone else's comment, replies posted by a bot account, and
    anything that is itself a marginal finding are left out, so only human
    answers to marginal come back. Threads keep GitHub's order, oldest first.
    """
    comments = list(comments)
    roots = {
        c["id"]: c
        for c in comments
        if c.get("id") is not None and not c.get("in_reply_to_id") and is_marginal_comment(_body(c))
    }
    replies: dict[object, list[str]] = {}
    for c in comments:
        parent = c.get("in_reply_to_id")
        body = _body(c).strip()
        user = c.get("user") or {}
        if parent in roots and body and not is_marginal_comment(body) and user.get("type") != "Bot":
            replies.setdefault(parent, []).append(body)
    return [
        ReplyThread(
            path=str(root.get("path", "")),
            # An outdated comment (its line pushed out of the diff) has
            # `line: null` but keeps `original_line`.
            line=root.get("line") or root.get("original_line"),
            comment=_MARKER.sub("", _body(root)).strip(),
            replies=tuple(replies[root_id]),
        )
        for root_id, root in roots.items()
        if root_id in replies
    ]


def body_finding_replies(
    reviews: Iterable[dict[str, object]], issue_comments: Iterable[dict[str, object]]
) -> list[ReplyThread]:
    """Maintainer PR comments answering marginal's review-body findings.

    A PR comment can't point at a finding, so each human comment (not a bot,
    not marginal's own text) posted after a review counts as a reply to
    every body finding in that review. Findings come back in review order,
    each with its later comments oldest first; one with none is left out.
    """
    answers = [
        (str(c["created_at"]), body)
        for c in issue_comments
        if c.get("created_at")
        and (body := _body(c).strip())
        and not is_marginal_comment(body)
        and (c.get("user") or {}).get("type") != "Bot"
    ]
    threads = []
    for review in reviews:
        submitted = review.get("submitted_at")
        replies = tuple(body for created, body in answers if submitted and created > str(submitted))
        if not replies:
            continue
        body = _body(review)
        start = 0
        for marker in _MARKER.finditer(body):
            badges = list(_BODY_BADGE.finditer(body, start, marker.start()))
            start = marker.end()
            if badges:
                finding = body[badges[-1].start() : marker.start()].strip()
                threads.append(ReplyThread(badges[-1][1], None, finding, replies))
    return threads


def _body(comment: dict[str, object]) -> str:
    return str(comment.get("body") or "")
