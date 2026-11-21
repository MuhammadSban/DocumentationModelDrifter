# fails on purpose, proves CI turns red (step 0.5)


def test_fails_on_purpose():
    assert False, "planted failure for the step 0.5 red check"
