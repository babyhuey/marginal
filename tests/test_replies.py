from marginal.review.dedup import fingerprint_marker
from marginal.review.replies import (
    ReplyThread,
    body_finding_replies,
    is_marginal_comment,
    maintainer_replies,
)

FINDING = (
    "🟡 **Medium** · 60% confidence\n\nThe ±1-line window can suppress a real neighbour.\n\n"
    + fingerprint_marker("0123456789abcdef")
)
# What releases before the fingerprint marker posted: the badge, no marker.
LEGACY_FINDING = "🟠 **High** · 80% confidence\n\nThis sleep blocks the event loop."

HUMAN = {"login": "maintainer", "type": "User"}
BOT = {"login": "github-actions[bot]", "type": "Bot"}


def comment(id, body, user=BOT, reply_to=None, path="dedup.py", line=58):
    c = {"id": id, "body": body, "user": user, "path": path, "line": line}
    if reply_to is not None:
        c["in_reply_to_id"] = reply_to
    return c


def test_a_maintainer_reply_to_a_marginal_finding_is_returned():
    threads = maintainer_replies(
        [comment(1, FINDING), comment(2, "Intentional trade-off.", HUMAN, reply_to=1)]
    )

    assert threads == [
        ReplyThread(
            path="dedup.py",
            line=58,
            comment="🟡 **Medium** · 60% confidence\n\nThe ±1-line window can suppress a "
            "real neighbour.",
            replies=("Intentional trade-off.",),
        )
    ]


def test_a_reply_to_a_legacy_unmarked_finding_is_returned():
    threads = maintainer_replies(
        [comment(1, LEGACY_FINDING), comment(2, "False positive.", HUMAN, reply_to=1)]
    )

    assert [t.replies for t in threads] == [("False positive.",)]


def test_a_reply_to_someone_elses_comment_is_ignored():
    threads = maintainer_replies(
        [
            comment(1, "Can we rename this?", HUMAN),
            comment(2, "Sure, done.", {"login": "author", "type": "User"}, reply_to=1),
        ]
    )

    assert threads == []


def test_a_marginal_finding_with_no_reply_is_ignored():
    assert maintainer_replies([comment(1, FINDING)]) == []


def test_bot_replies_and_marginal_findings_in_a_thread_are_not_maintainer_replies():
    threads = maintainer_replies(
        [
            comment(1, FINDING),
            comment(2, "Automated note.", BOT, reply_to=1),
            # A finding body under the thread is marginal's, whoever posted it.
            comment(3, LEGACY_FINDING, HUMAN, reply_to=1),
            comment(4, "   ", HUMAN, reply_to=1),
        ]
    )

    assert threads == []


def test_every_reply_in_a_thread_is_kept_in_order():
    threads = maintainer_replies(
        [
            comment(1, FINDING),
            comment(2, "First answer.", HUMAN, reply_to=1),
            comment(3, "Follow-up.", {"login": "other", "type": "User"}, reply_to=1),
        ]
    )

    assert threads[0].replies == ("First answer.", "Follow-up.")


def test_an_outdated_comment_falls_back_to_its_original_line():
    root = comment(1, FINDING, line=None)
    root["original_line"] = 56

    threads = maintainer_replies([root, comment(2, "Answered.", HUMAN, reply_to=1)])

    assert threads[0].line == 56


def test_is_marginal_comment_needs_the_marker_or_a_leading_badge():
    assert is_marginal_comment(FINDING)
    assert is_marginal_comment(LEGACY_FINDING)
    assert not is_marginal_comment("I think 🟡 **Medium** · 60% confidence was too low.")
    assert not is_marginal_comment("Looks good")
    assert not is_marginal_comment(None)


# -- answers to review-body findings, posted as PR comments ----------------

BODY_FINDING_A = (
    "🟠 **High** · 60% confidence — `marginal/cli/init.py`\n\nThe template drops `types:`."
)
BODY_FINDING_B = "🟡 **Medium** · 70% confidence — `README.md`\n\nThe checkout step is gone."


def review(*findings, at="2026-10-17T15:01:10Z"):
    body = "### 🤖 marginal review\n\n**2 findings**\n"
    for n, finding in enumerate(findings):
        body += f"\n{finding}\n{fingerprint_marker(f'{n:016x}')}"
    return {"body": body, "user": BOT, "submitted_at": at}


def pr_comment(body, at="2026-10-17T15:02:25Z", user=HUMAN):
    return {"body": body, "user": user, "created_at": at}


def test_a_later_pr_comment_answers_every_body_finding_of_the_review():
    threads = body_finding_replies(
        [review(BODY_FINDING_A, BODY_FINDING_B)], [pr_comment("Both are false positives.")]
    )

    assert threads == [
        ReplyThread("marginal/cli/init.py", None, BODY_FINDING_A, ("Both are false positives.",)),
        ReplyThread("README.md", None, BODY_FINDING_B, ("Both are false positives.",)),
    ]


def test_pr_comments_before_the_review_bots_and_marginal_text_are_not_answers():
    threads = body_finding_replies(
        [review(BODY_FINDING_A)],
        [
            pr_comment("Posted before marginal reviewed.", at="2026-10-17T15:00:00Z"),
            pr_comment("Automated note.", user=BOT),
            pr_comment(LEGACY_FINDING),
            pr_comment("   "),
        ],
    )

    assert threads == []


def test_only_reviews_older_than_the_comment_get_it():
    first = review(BODY_FINDING_A, at="2026-10-17T15:00:00Z")
    second = review(BODY_FINDING_B, at="2026-10-17T16:00:00Z")

    threads = body_finding_replies(
        [first, second], [pr_comment("Answering the first.", at="2026-10-17T15:30:00Z")]
    )

    assert [t.path for t in threads] == ["marginal/cli/init.py"]


def test_a_review_with_no_body_findings_has_nothing_to_answer():
    no_findings = {"body": "### 🤖 marginal review\n\n✅ **No issues found**", "user": BOT}
    no_findings["submitted_at"] = "2026-10-17T15:01:10Z"

    assert body_finding_replies([no_findings], [pr_comment("Thanks!")]) == []
