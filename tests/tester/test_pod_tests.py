# tests the pod test runner against the fake target: outcomes, skips, errors, coverage and the run limit

from Tester.pod_tests import LIMIT_REACHED, PENDING, TESTS, run_suite

IDS = [t.id for t in TESTS]


def outcomes(report):
    # maps each test id to its result entry
    return {r["test_id"]: r for r in report["results"]}


def ids(first, last):
    return IDS[IDS.index(first): IDS.index(last) + 1]


def test_table_has_33_tests_in_order():
    assert IDS == [f"T-{i:02d}" for i in range(1, 34)]


def test_target_meeting_the_contract_passes_everything_it_runs(fake):
    report = run_suite(fake.url, "s1")
    got = outcomes(report)
    assert [r["test_id"] for r in report["results"]] == IDS
    assert {got[t]["outcome"] for t in ids("T-01", "T-21")} == {"pass"}
    assert got["T-22"] == {"message": "Phase 5", "outcome": "skip", "test_id": "T-22"}
    assert got["T-23"]["message"] == "checked by inspection"
    assert {got[t]["message"] for t in ids("T-24", "T-33")} == {PENDING}
    assert report["coverage"]["component"]["covered"] == 6  # all but C7, which only T-22 lists
    assert report["coverage"]["system"]["covered"] == 8  # all but AC-05 (T-22) and AC-09 (T-23)
    assert report["coverage"]["code"] == {"basis": "fake line coverage", "covered": 3, "total": 10}
    assert report["session_id"] == "s1" and report["target_url"] == fake.url


def test_each_result_is_handed_over_as_it_is_decided(fake):
    seen = []
    report = run_suite(fake.url, "s", on_result=lambda entry: seen.append((len(seen) + 1, entry)))
    assert [entry for _, entry in seen] == report["results"]
    assert [n for n, _ in seen] == list(range(1, 34))


def test_missing_feature_is_skipped_not_failed(fake):
    fake.features = ["model_drift"]
    got = outcomes(run_suite(fake.url, "s"))
    assert {got[t]["message"] for t in ids("T-18", "T-21")} == {"target does not implement prose_detector"}
    assert {got[t]["outcome"] for t in ids("T-01", "T-17")} == {"pass"}


def test_failed_health_errors_only_the_tests_that_need_a_feature(fake):
    fake.health_status = 500
    got = outcomes(run_suite(fake.url, "s"))
    assert {(got[t]["outcome"], got[t]["source"]) for t in ids("T-18", "T-21")} == {("error", "system")}
    assert {got[t]["message"] for t in ids("T-24", "T-33")} == {PENDING}
    assert got["T-01"]["outcome"] == "pass"


def test_unreachable_target_is_a_communication_error(closed_url):
    report = run_suite(closed_url, "s")
    got = outcomes(report)
    assert (got["T-01"]["outcome"], got["T-01"]["source"]) == ("error", "communication")
    assert (got["T-18"]["outcome"], got["T-18"]["source"]) == ("error", "communication")
    assert report["coverage"]["component"]["covered"] == 0
    assert report["coverage"]["code"]["covered"] is None and report["coverage"]["code"]["total"] is None


def test_5xx_is_a_system_error_that_still_counts_as_answered(fake):
    fake.analyze_status = 500
    report = run_suite(fake.url, "s")
    got = outcomes(report)
    assert (got["T-01"]["outcome"], got["T-01"]["source"]) == ("error", "system")
    assert got["T-15"]["outcome"] == "pass"  # GET of an unknown id never reaches /analyze
    assert report["coverage"]["component"]["covered"] == 6


def test_golden_mismatch_fails_and_names_the_field(fake):
    fake.break_case = "c1-impl-only"
    got = outcomes(run_suite(fake.url, "s"))
    assert got["T-01"]["outcome"] == "fail"
    assert "changes" in got["T-01"]["message"]
    assert got["T-02"]["outcome"] == "pass"


def test_run_limit_ends_the_test_in_progress_and_skips_the_rest(fake):
    fake.analyze_delay = 0.4
    report = run_suite(fake.url, "s", limit=0.6)
    got = outcomes(report)
    assert got["T-01"]["outcome"] == "pass"
    assert got["T-02"] == {"message": LIMIT_REACHED, "outcome": "error", "source": "tester", "test_id": "T-02"}
    assert {(got[t]["outcome"], got[t]["message"]) for t in ids("T-03", "T-33")} == {("skip", LIMIT_REACHED)}
    assert report["coverage"]["code"]["covered"] is None
