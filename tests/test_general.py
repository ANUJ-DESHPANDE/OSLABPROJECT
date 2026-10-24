"""Checks cautious code review and local-model response validation."""

import unittest
from unittest.mock import patch
import json

from oslab.code_review import inspect_code, pipe_eof_walkthrough, retrieval_query
from oslab.local_model import explain
from oslab.visuals import choose_visual


class GeneralToolTests(unittest.TestCase):
    def test_question_selects_reusable_mechanism(self):
        self.assertEqual(choose_visual("Why does a page fault occur?")["id"], "page_fault")
        self.assertEqual(choose_visual("How does round robin work?")["id"], "scheduling")
        self.assertEqual(choose_visual("How does a semaphore work?")["id"], "synchronization")
        self.assertIsNone(choose_visual("What is an operating system?"))

    def test_code_inspection_is_conditional_and_topic_aware(self):
        pipe = inspect_code("int fds[2]; pipe(fds); read(fds[0], b, 1);")
        self.assertIn("pipes", pipe["topics"])
        self.assertIn("unused pipe ends", pipe["findings"][0]["next_check"])
        self.assertIn("file descriptor", retrieval_query("Why does read hang?", pipe))
        self.assertEqual(choose_visual("", [], pipe["topics"])["id"], "pipe")

    def test_comments_do_not_count_as_calls(self):
        result = inspect_code("// fork() and pipe() are examples\nint main(void) { return 0; }")
        self.assertNotIn("processes", result["topics"])
        self.assertNotIn("pipes", result["topics"])

    def test_pipe_eof_loop_hypothesis_has_exact_source_lines(self):
        code = "pipe(fds);\nfork();\nwhile (read(fds[0], buf, 8) > 0) {}\nwait(NULL);"
        result = inspect_code(code)
        self.assertIn("close every unused pipe write end", result["findings"][1]["next_check"])
        self.assertEqual(result["findings"][1]["lines"], [2, 3, 4])
        self.assertEqual(result["execution_status"], "not_executed")

    def test_pipe_eof_walkthrough_keeps_code_and_source_evidence(self):
        code = "pipe(fds);\nfork();\nwhile (read(fds[0], buf, 8) > 0) {}\nwrite(fds[1], buf, 8);\nwait(NULL);"
        source = {"text": "A pipe reader sees EOF only after all write ends close."}
        result = pipe_eof_walkthrough(code, inspect_code(code), [source])
        self.assertEqual(result["origin"], "static")
        self.assertIn("line 3", result["answer"])
        self.assertEqual([step["code_line"] for step in result["visual"]["steps"][:4]], [1, 3, 4, 5])
        self.assertIn("[1]", result["answer"])

    def test_source_clue_keeps_line_after_multiline_comment(self):
        result = inspect_code("/* note\npipe(x); */\nint main(void) { pipe(fd); }")
        self.assertEqual(result["findings"][0]["lines"], [3])

    def test_semaphore_and_file_calls_are_routed(self):
        result = inspect_code("sem_wait(&s);\nint fd = open(path, 0);")
        self.assertEqual(result["topics"], ["semaphores", "files"])
        self.assertEqual([item["lines"] for item in result["findings"]], [[1], [2]])

    def test_model_rejects_citation_it_was_not_given(self):
        source = {"title": "Paging", "location": "slide 1", "source": "paging.pptx",
                  "text": "A page fault traps to the operating system."}
        response = {"coverage": "supported", "answer_points": [{"claim": "A page fault traps to the OS.", "source_id": 2}], "visual_title": "Fault",
                    "visual_steps": [{"label": "Trap", "detail": "The OS handles it.",
                                      "source_id": 1, "code_line": 0}] * 3}
        with patch("oslab.local_model.status", return_value={"ready": True, "provider": "llama.cpp", "model": "local"}), \
             patch("oslab.local_model._request", return_value={"choices": [{"message": {"content": json.dumps(response)}}]}):
            with self.assertRaisesRegex(RuntimeError, "source-cited"):
                explain("What is a page fault?", [source])

    def test_model_attaches_checked_citation_and_visual_source(self):
        source = {"title": "Paging", "location": "slide 1", "source": "paging.pptx",
                  "text": "A page fault traps to the operating system."}
        response = {"coverage": "supported", "answer_points": [{"claim": "A page fault traps to the OS.", "source_id": 1}],
                    "visual_title": "Fault", "visual_steps": [
                        {"label": label, "detail": "The OS handles it.", "source_id": 1, "code_line": 0}
                        for label in ("Access", "Trap", "Handle")]}
        with patch("oslab.local_model.status", return_value={"ready": True, "provider": "llama.cpp", "model": "local"}), \
             patch("oslab.local_model._request", return_value={"choices": [{"message": {"content": json.dumps(response)}}]}):
            result = explain("What is a page fault?", [source])
        self.assertEqual(result["answer"], "A page fault traps to the OS. [1]")
        self.assertEqual(result["visual"]["steps"][0]["source_id"], 1)

    def test_partial_source_coverage_suppresses_generated_claims(self):
        source = {"title": "Disk", "location": "slide 1", "source": "disk.pptx",
                  "text": "Disk scheduling is part of secondary-storage management."}
        response = {"coverage": "partial", "answer_points": [
            {"claim": "FCFS and SSTF use different seek strategies.", "source_id": 1}],
            "visual_title": "", "visual_steps": []}
        with patch("oslab.local_model.status", return_value={"ready": True, "provider": "llama.cpp", "model": "local"}), \
             patch("oslab.local_model._request", return_value={"choices": [{"message": {"content": json.dumps(response)}}]}):
            with self.assertRaisesRegex(RuntimeError, "do not cover enough"):
                explain("Compare FCFS and SSTF disk scheduling", [source])


if __name__ == "__main__":
    unittest.main()
