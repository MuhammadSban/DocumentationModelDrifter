# tests the pod test runner against the fake target: outcomes, skips, errors, coverage and the run limit

from pathlib import Path

import jsonschema
import yaml

from Tester import pod_tests
from Tester.pod_tests import LIMIT_REACHED, REQUIREMENTS_MAP, TESTS, read_requirements_map, requirement_tests, \
    run_suite

IDS = [t.id for t in TESTS]


def outcomes(report):
    # maps each test id to its result entry
    return {r["test_id"]: r for r in report["results"]}


def ids(first, last):
    return IDS[IDS.index(first): IDS.index(last) + 1]


def test_table_has_33_tests_in_order():
    assert IDS == [f"T-{i:02d}" for i in range(1, 34)]


def test_map_reader_returns_the_version_and_seven_requirements_with_their_criteria():
    version, requirements = read_requirements_map()
    assert version == "1"
    assert requirements == {
        "REQ-01": ("AC-01",), "REQ-02": ("AC-02", "AC-03"), "REQ-03": ("AC-04", "AC-05"), "REQ-04": ("AC-06",),
        "REQ-05": ("AC-07", "AC-08"), "REQ-06": ("AC-09",), "REQ-07": ("AC-03", "AC-10"),
    }


def test_map_table_equals_the_tests_derived_from_the_test_list():
    rows = [line.split("|")[1:4] for line in REQUIREMENTS_MAP.read_text(encoding="utf-8").splitlines()
            if line.startswith("| REQ-")]
    table = {r.strip(): (tuple(c.strip().split(", ")), tuple(t.strip().split(", "))) for r, c, t in rows}
    _, requirements = read_requirements_map()
    derived = requirement_tests(requirements)
    assert table == {r: (requirements[r], derived[r]) for r in requirements}


def test_target_meeting_the_contract_passes_everything_it_runs(fake):
    report = run_suite(fake.url, "s1")
    got = outcomes(report)
    assert [r["test_id"] for r in report["results"]] == IDS
    assert {got[t]["outcome"] for t in ids("T-01", "T-21")} == {"pass"}
    assert got["T-22"] == {"message": "target does not implement model_drift", "outcome": "skip",
                           "test_id": "T-22"}
    assert got["T-23"]["outcome"] == "pass"  # runs on every system (contract §4)
    assert {got[t]["message"] for t in ids("T-24", "T-33")} == {"target does not implement model_drift"}
    assert report["coverage"]["component"]["covered"] == 6  # all but C7, which only T-22 lists
    assert report["coverage"]["system"]["covered"] == 9  # all but AC-05, whose only test, T-22, skips
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
    assert {got[t]["message"] for t in ids("T-18", "T-20")} == {"target does not implement prose_detector"}
    assert got["T-21"]["outcome"] == "pass"  # runs its model version instead
    assert {got[t]["outcome"] for t in ids("T-01", "T-17")} == {"pass"}


def test_failed_health_errors_only_the_tests_that_need_a_feature(fake):
    fake.health_status = 500
    got = outcomes(run_suite(fake.url, "s"))
    assert {(got[t]["outcome"], got[t]["source"]) for t in ids("T-18", "T-21")} == {("error", "system")}
    assert {(got[t]["outcome"], got[t]["source"]) for t in ids("T-24", "T-33")} == {("error", "system")}
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
    assert report["coverage"]["system"]["covered"] == 2  # only T-15 passes: AC-06 and AC-08


def test_system_does_not_count_a_skipped_test(fake):
    # leaves out AC-05, whose only test, T-22, skips without model_drift
    system = run_suite(fake.url, "s")["coverage"]["system"]
    assert (system["covered"], system["total"]) == (9, 10)


def test_system_does_not_count_an_error_from_communication(closed_url):
    assert run_suite(closed_url, "s")["coverage"]["system"]["covered"] == 0


def test_system_does_not_count_an_error_from_the_tester(fake):
    # ends T-01 as error with source tester at the run limit, and skips the rest
    fake.analyze_delay = 0.4
    report = run_suite(fake.url, "s", limit=0.2)
    assert (outcomes(report)["T-01"]["outcome"], outcomes(report)["T-01"]["source"]) == ("error", "tester")
    assert report["coverage"]["system"]["covered"] == 0


def test_system_does_not_count_an_error_when_health_fails(fake):
    # counts only T-01 to T-17, which pass: AC-01, AC-06, AC-07, AC-08 and AC-10
    fake.health_status = 500
    assert run_suite(fake.url, "s")["coverage"]["system"]["covered"] == 5


def test_system_counts_a_criterion_listed_by_two_evaluated_tests_once(fake):
    # counts AC-01 once though T-01 to T-07 pass, and AC-02 once though T-18, T-19, T-26 to T-28, T-30, T-31 pass
    fake.features = ["prose_detector", "model_drift"]
    report = run_suite(fake.url, "s")
    assert {outcomes(report)[t]["outcome"] for t in ids("T-01", "T-33")} == {"pass"}
    system = report["coverage"]["system"]
    assert (system["covered"], system["total"]) == (10, 10)


def test_system_basis_names_pass_or_fail_and_ac_11(fake):
    basis = run_suite(fake.url, "s")["coverage"]["system"]["basis"]
    for part in ("AC-01 to AC-10", "pass or fail", "AC-11", "pod-contract.md section 5",
                 "specifications.md section 4.1"):
        assert part in basis


def test_component_basis_keeps_the_answered_wording(fake):
    basis = run_suite(fake.url, "s")["coverage"]["component"]["basis"]
    assert basis == "components C1 to C7 exercised by a test the target answered (pod-contract.md section 5)"


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


def test_drift_tests_pass_when_every_case_gives_its_expected_drift(fake):
    fake.features = ["model_drift"]
    got = outcomes(run_suite(fake.url, "s"))
    assert {got[t]["outcome"] for t in ids("T-24", "T-31")} == {"pass"}
    assert got["T-28"]["message"] == "L4 matches the expected answer"


def test_t32_passes_when_l_pre_gives_models_not_found(fake):
    fake.features = ["model_drift"]
    got = outcomes(run_suite(fake.url, "s"))
    assert got["T-32"]["outcome"] == "pass"


def test_t32_fails_naming_the_case_and_field_when_drift_error_differs(fake):
    fake.features = ["model_drift"]
    fake.break_drift_case = "L-pre"
    got = outcomes(run_suite(fake.url, "s"))
    assert got["T-32"]["outcome"] == "fail"
    assert "L-pre" in got["T-32"]["message"] and "drift_error" in got["T-32"]["message"]


def test_a_drift_test_fails_naming_the_case_and_field_when_only_the_order_differs(fake):
    fake.features = ["model_drift"]
    fake.break_drift_case = "L4"
    got = outcomes(run_suite(fake.url, "s"))
    assert got["T-28"] == {"message": "L4: drift differs from the expected answer", "outcome": "fail",
                           "test_id": "T-28"}
    assert got["T-26"]["outcome"] == "pass"


def test_t33_passes_when_generate_returns_the_three_texts(fake):
    fake.features = ["model_drift"]
    got = outcomes(run_suite(fake.url, "s"))
    assert got["T-33"] == {"message": "L0-generate: the three texts match the expected answer", "outcome": "pass",
                           "test_id": "T-33"}


def test_t33_fails_naming_the_case_and_file_when_a_text_differs(fake):
    fake.features = ["model_drift"]
    fake.break_generate = "behavioral.json"
    got = outcomes(run_suite(fake.url, "s"))
    assert got["T-33"] == {"message": "L0-generate: behavioral.json differs from the expected text",
                           "outcome": "fail", "test_id": "T-33"}


def test_t21_run_uses_the_model_version_with_only_model_drift(fake):
    fake.features = ["model_drift"]
    got = outcomes(run_suite(fake.url, "s"))
    assert got["T-21"] == {"message": "L2: two answers match the expected answer", "outcome": "pass",
                           "test_id": "T-21"}


def test_t21_run_fails_when_the_second_answer_differs(fake):
    # flips only the second answer for L2, so a check of the first answer alone would pass
    fake.features = ["model_drift"]
    fake.flip_aligned_case, fake.flip_aligned_from = "L2", 2
    got = outcomes(run_suite(fake.url, "s"))
    assert got["T-21"] == {"message": "L2: drift differs from the expected answer", "outcome": "fail",
                           "test_id": "T-21"}


def test_t21_run_keeps_the_prose_version_with_prose_detector(fake):
    got = outcomes(run_suite(fake.url, "s"))
    assert got["T-21"] == {"message": "all 3 findings start PENDING_REVIEW", "outcome": "pass", "test_id": "T-21"}


def test_t21_run_keeps_the_prose_version_with_both_features(fake):
    fake.features = ["prose_detector", "model_drift"]
    got = outcomes(run_suite(fake.url, "s"))
    assert got["T-21"] == {"message": "all 3 findings start PENDING_REVIEW", "outcome": "pass", "test_id": "T-21"}


def test_t21_run_skips_with_neither_feature(fake):
    fake.features = []
    got = outcomes(run_suite(fake.url, "s"))
    assert got["T-21"] == {"message": "target does not implement prose_detector", "outcome": "skip",
                           "test_id": "T-21"}


def test_t22_run_passes_with_model_drift(fake):
    fake.features = ["model_drift"]
    got = outcomes(run_suite(fake.url, "s"))
    assert got["T-22"] == {"message": "L5 and L6 match the expected answers", "outcome": "pass", "test_id": "T-22"}


def test_t22_run_fails_when_the_unauthorized_change_is_not_flagged(fake):
    # answers L6, a non-owner's edit, as aligned
    fake.features = ["model_drift"]
    fake.flip_aligned_case = "L6"
    got = outcomes(run_suite(fake.url, "s"))
    assert got["T-22"] == {"message": "L6: drift differs from the expected answer", "outcome": "fail",
                           "test_id": "T-22"}


def test_t22_run_fails_when_the_authorized_change_is_flagged(fake):
    # answers L5, an owner's change with /models updated, as not aligned
    fake.features = ["model_drift"]
    fake.flip_aligned_case = "L5"
    got = outcomes(run_suite(fake.url, "s"))
    assert got["T-22"] == {"message": "L5: drift differs from the expected answer", "outcome": "fail",
                           "test_id": "T-22"}


def test_t22_run_skips_without_model_drift(fake):
    assert outcomes(run_suite(fake.url, "s"))["T-22"]["outcome"] == "skip"


def test_t23_run_passes_with_model_drift(fake):
    fake.features = ["model_drift"]
    got = outcomes(run_suite(fake.url, "s"))
    assert got["T-23"] == {"message": "L8 matches the expected answer", "outcome": "pass", "test_id": "T-23"}


def test_t23_run_fails_when_the_answer_differs(fake):
    fake.features = ["model_drift"]
    fake.flip_aligned_case = "L8"
    got = outcomes(run_suite(fake.url, "s"))
    assert got["T-23"] == {"message": "L8: drift differs from the expected answer", "outcome": "fail",
                           "test_id": "T-23"}


def test_t23_run_passes_on_a_system_without_model_drift(fake):
    # asks a system that judges no drift only for a normal answer to L8, which shows its code was not run
    got = outcomes(run_suite(fake.url, "s"))
    assert got["T-23"] == {"message": "L8 was analyzed and answered SUCCESS", "outcome": "pass", "test_id": "T-23"}


def test_t23_run_fails_without_model_drift_when_the_answer_is_not_a_success(fake):
    fake.model_status = "ERROR"
    got = outcomes(run_suite(fake.url, "s"))
    assert got["T-23"] == {"message": "L8: status is 'ERROR', not SUCCESS", "outcome": "fail", "test_id": "T-23"}


def test_full_coverage_system_is_10_of_10_with_model_drift(fake):
    # covers every criterion though T-18 to T-20 skip: AC-04 by T-21's model version, AC-05 by T-22, AC-09 by T-23
    fake.features = ["model_drift"]
    report = run_suite(fake.url, "s")
    assert [r["test_id"] for r in report["results"] if r["outcome"] != "pass"] == ids("T-18", "T-20")
    system = report["coverage"]["system"]
    assert (system["covered"], system["total"]) == (10, 10)


def model_of(report):
    return report["coverage"]["model"]


def test_model_is_present_for_our_own_system_with_total_7_and_covered_at_most_total(fake):
    model = model_of(run_suite(fake.url, "s1", own=True))
    assert model["total"] == 7 and 0 <= model["covered"] <= model["total"]
    assert "version 1" in model["basis"] and "requirements-to-tests.md" in model["basis"]


def test_model_counts_a_requirement_with_no_evaluated_test_in_total(fake):
    # keeps REQ-02 and REQ-03 in total, though with neither feature all their tests skip
    fake.features = []
    model = model_of(run_suite(fake.url, "s1", own=True))
    assert (model["covered"], model["total"]) == (5, 7)


def test_model_does_not_cover_a_requirement_whose_tests_ended_skip_or_error(fake):
    # drops REQ-02 and REQ-03 when their tests skip with neither feature; REQ-01, REQ-04, REQ-05 and
    # REQ-07 stay, from T-01 to T-17, and REQ-06 from T-23, which runs on every system
    fake.features = []
    assert model_of(run_suite(fake.url, "s1", own=True))["covered"] == 5
    # leaves out a 5xx, error with source system, as system coverage does; with every /analyze
    # answering 500 only T-15 passes, and its AC-06 and AC-08 cover REQ-04 and REQ-05 (spec §4.1)
    fake.features = None
    fake.analyze_status = 500
    report = run_suite(fake.url, "s2", own=True)
    assert [r["test_id"] for r in report["results"] if r["outcome"] in ("pass", "fail")] == ["T-15"]
    assert model_of(report)["covered"] == 2
    assert report["coverage"]["system"]["covered"] == 2


def test_model_counts_a_requirement_listed_by_two_evaluated_tests_once(fake):
    # counts REQ-01 once, though seven of its tests, T-01 to T-07, pass
    report = run_suite(fake.url, "s1", own=True)
    assert {outcomes(report)[t]["outcome"] for t in ids("T-01", "T-07")} == {"pass"}
    assert model_of(report)["covered"] == 7


def test_model_key_is_absent_for_another_system(fake):
    assert "model" not in run_suite(fake.url, "s1")["coverage"]
    assert "model" not in run_suite(fake.url, "s2", own=False)["coverage"]


def test_model_report_validates_against_the_pod_tester_openapi(fake):
    spec = Path(pod_tests.CONTRACT, "pod-tester.openapi.yml").read_text(encoding="utf-8")
    components = yaml.safe_load(spec)["components"]
    report = run_suite(fake.url, "s1", own=True)
    for name, value in (("SuiteReport", report), ("CoverageMeasure", model_of(report))):
        jsonschema.validate(value, {"$ref": f"#/components/schemas/{name}", "components": components})


def test_model_unreadable_map_gives_null_counts_and_a_basis_saying_why(fake, monkeypatch, tmp_path):
    monkeypatch.setattr(pod_tests, "REQUIREMENTS_MAP", tmp_path / "missing.md")
    model = model_of(run_suite(fake.url, "s1", own=True))
    assert model["covered"] is None and model["total"] is None
    assert "unavailable" in model["basis"] and "missing.md" in model["basis"]


def test_full_coverage_model_is_7_of_7_on_our_own_system(fake):
    # covers REQ-03 by T-21 and T-22 and REQ-06 by T-23, as on our own system, which lists only model_drift
    fake.features = ["model_drift"]
    model = model_of(run_suite(fake.url, "s1", own=True))
    assert (model["covered"], model["total"]) == (7, 7)
