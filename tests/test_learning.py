import unittest

from oslab.concepts import load_concepts
from oslab.process_model import apply_event, grade_prediction, initial_state, scenario
from oslab.studio import audit_demo
from oslab.evaluate import processing_evaluation
from oslab.scheduling import simulate


class DatasetStudioTests(unittest.TestCase):
    def test_audit_has_provenance_and_health(self):
        audit = audit_demo()
        self.assertEqual(audit["knowledge"]["health"]["source_count"], 3)
        self.assertEqual(audit["knowledge"]["health"]["record_count"], 21)
        self.assertEqual(audit["behaviour"]["health"]["case_count"], 5)
        self.assertEqual(audit["behaviour"]["health"]["observed_trace_count"], 0)
        self.assertTrue(audit["knowledge"]["sources"][0]["sections"])
        self.assertTrue(audit["behaviour"]["cases"][1]["source_diff"])

    def test_concept_links_resolve(self):
        audit = audit_demo()
        self.assertEqual(audit["knowledge"]["health"]["warnings"], [])
        self.assertEqual({item["id"] for item in load_concepts()}, {"process", "fork", "wait", "exec", "scheduling", "round_robin"})

    def test_labelled_processing_benchmark(self):
        result = processing_evaluation()
        self.assertEqual(result["labelled_section_count"], 21)
        self.assertEqual(result["section_heading_recall"], 1.0)
        self.assertEqual(result["metadata_completeness"], 1.0)


class ProcessModelTests(unittest.TestCase):
    def test_wait_orders_completion_and_reaps_child(self):
        frames = scenario(True)["frames"]
        events = [frame["event"] for frame in frames]
        self.assertLess(events.index("CHILD_EXIT"), events.index("PARENT_OUTPUT"))
        self.assertTrue(frames[-1]["state"]["child_reaped"])
        self.assertEqual(frames[-1]["state"]["output"], ["child finished", "parent complete"])

    def test_no_wait_has_two_valid_schedules(self):
        first = scenario(False, "parent_first")["frames"][-1]["state"]["output"]
        second = scenario(False, "child_first")["frames"][-1]["state"]["output"]
        self.assertEqual(first, ["parent complete", "child finished"])
        self.assertEqual(second, ["child finished", "parent complete"])

    def test_child_first_wait_returns_after_exit(self):
        frames = scenario(True, "child_first")["frames"]
        events = [frame["event"] for frame in frames]
        self.assertLess(events.index("CHILD_EXIT"), events.index("PARENT_WAIT_IMMEDIATE"))
        self.assertTrue(frames[-1]["state"]["child_reaped"])

    def test_reducer_rejects_impossible_transition(self):
        with self.assertRaises(AssertionError):
            apply_event(initial_state(), "PARENT_WAIT")

    def test_prediction_grading_uses_model(self):
        correct = grade_prediction(True, "parent_first", 1, "PARENT_WAIT")
        wrong = grade_prediction(True, "parent_first", 1, "CHILD_RUN")
        self.assertTrue(correct["correct"])
        self.assertFalse(wrong["correct"])
        self.assertEqual(wrong["misconception_id"], "fork_runs_child_first")


class SchedulingTests(unittest.TestCase):
    workload = [{"id": "P1", "arrival": 0, "burst": 4},
                {"id": "P2", "arrival": 1, "burst": 3},
                {"id": "P3", "arrival": 2, "burst": 1}]

    def test_fcfs_known_timeline_and_metrics(self):
        result = simulate(self.workload, "FCFS")
        self.assertEqual([slot["process"] for slot in result["gantt"]], ["P1"]*4 + ["P2"]*3 + ["P3"])
        self.assertEqual(result["metrics"]["P2"], {"waiting": 3, "turnaround": 6, "response": 3, "completion": 7})

    def test_sjf_reorders_ready_queue(self):
        result = simulate(self.workload, "SJF")
        self.assertEqual([slot["process"] for slot in result["gantt"]], ["P1"]*4 + ["P3"] + ["P2"]*3)
        self.assertEqual(result["metrics"]["P3"]["waiting"], 2)

    def test_round_robin_quantum_and_arrivals(self):
        result = simulate(self.workload, "RR", 2)
        self.assertEqual([slot["process"] for slot in result["gantt"]], ["P1","P1","P2","P2","P1","P1","P3","P2"])
        self.assertEqual(result["metrics"]["P3"]["response"], 4)

    def test_invalid_workload_rejected(self):
        with self.assertRaises(ValueError):
            simulate([{"id":"P1","arrival":0,"burst":0}], "RR", 2)


if __name__ == "__main__":
    unittest.main()
