from marginal.review.dedup import finding_fingerprint, fingerprint_marker, posted_fingerprints

PATCH = (
    "@@ -10,3 +10,4 @@ def retry():\n"
    "     attempts = 0\n"
    "-    time.sleep(0)\n"
    "+    time.sleep(1)\n"
    "     return attempts\n"
)


def test_same_line_text_matches_despite_reworded_message():
    first = finding_fingerprint("retry.py", 11, "Blocking sleep in async loop.", PATCH)
    second = finding_fingerprint("retry.py", 11, "time.sleep blocks the event loop here", PATCH)

    assert first == second


def test_same_line_text_matches_after_the_line_shifts():
    shifted = PATCH.replace("+10,4", "+14,4")

    assert finding_fingerprint("retry.py", 11, "x", PATCH) == finding_fingerprint(
        "retry.py", 15, "x", shifted
    )


def test_different_line_text_differs():
    changed = PATCH.replace("+    time.sleep(1)", "+    await asyncio.sleep(1)")

    assert finding_fingerprint("retry.py", 11, "x", PATCH) != finding_fingerprint(
        "retry.py", 11, "x", changed
    )


def test_line_text_ignores_whitespace_changes():
    reindented = PATCH.replace("+    time.sleep(1)", "+\t\ttime.sleep(1)  ")

    assert finding_fingerprint("retry.py", 11, "x", PATCH) == finding_fingerprint(
        "retry.py", 11, "x", reindented
    )


def test_different_file_differs():
    assert finding_fingerprint("a.py", 11, "x", PATCH) != finding_fingerprint(
        "b.py", 11, "x", PATCH
    )


def test_line_outside_the_patch_falls_back_to_its_number():
    assert finding_fingerprint("retry.py", 99, "x", PATCH) == finding_fingerprint(
        "retry.py", 99, "something else", None
    )
    assert finding_fingerprint("retry.py", 99, "x", PATCH) != finding_fingerprint(
        "retry.py", 98, "x", PATCH
    )


def test_unanchored_finding_uses_normalized_message():
    assert finding_fingerprint("a.py", None, "Add  a Backoff cap.", None) == finding_fingerprint(
        "a.py", None, "add a backoff\ncap.", None
    )
    assert finding_fingerprint("a.py", None, "Add a backoff cap.", None) != finding_fingerprint(
        "a.py", None, "Add a retry limit.", None
    )


def test_secret_on_the_line_does_not_leak_into_the_hash():
    def with_key(key):
        return f"@@ -1 +1 @@\n+api_key = '{key}'\n"

    # Both lines redact to the same text, so the hash can't depend on the secret.
    assert finding_fingerprint("c.py", 1, "x", with_key("AKIAIOSFODNN7EXAMPLE")) == (
        finding_fingerprint("c.py", 1, "x", with_key("AKIAZZZZZZZZZZZZZZZZ"))
    )


def test_posted_fingerprints_reads_markers_from_bodies():
    bodies = [
        f"🟠 **High**\n\nissue\n\n{fingerprint_marker('0123456789abcdef')}",
        None,
        "a human reply with no marker",
        f"summary\n{fingerprint_marker('fedcba9876543210')}",
    ]

    assert posted_fingerprints(bodies) == {"0123456789abcdef", "fedcba9876543210"}
