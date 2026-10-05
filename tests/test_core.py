import tempfile
import unittest
from pathlib import Path

from oslab.behaviour import build_cases, normalize_trace, static_features
from oslab.diagnose import diagnose
from oslab.knowledge import Retriever, ingest, load_demo, parse_markdown, section_chunks


class KnowledgeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.records = load_demo()
        cls.retriever = Retriever(cls.records)

    def test_document_sections_and_metadata(self):
        records = parse_markdown("data/demo/fork_wait.md")
        self.assertEqual(len(records), 7)
        self.assertEqual(records[0]["section_type"], "Aim")
        self.assertEqual(records[0]["experiment_id"], "FW01")
        self.assertEqual(len(records[0]["content_hash"]), 64)
        self.assertEqual(records[0]["source"], "fork_wait.md")

    def test_deduplication(self):
        records = ingest(["data/demo/fork_wait.md", "data/demo/fork_wait.md"])
        self.assertEqual(len(records), 7)

    def test_large_section_split(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "long.md"
            path.write_text("# Experiment T01: Test\n## Theory\n" + "fork " * 710, encoding="utf-8")
            self.assertEqual(len(parse_markdown(path)), 3)

    def test_fenced_program_preserves_layout(self):
        content = "First paragraph.\n\n```c\nint main(void) {\n    return 0;\n}\n```\n\nSecond paragraph."
        chunks = section_chunks(content, max_words=8)
        self.assertIn("int main(void) {\n    return 0;\n}", "\n".join(chunks))
        self.assertEqual(len(chunks), 3)

    def test_metadata_filter(self):
        for method in ("bm25", "dense", "hybrid"):
            got = self.retriever.search("wait parent", "FW01", method=method)
            self.assertTrue(got)
            self.assertTrue(all(r["experiment_id"] == "FW01" for r in got))

    def test_retrieval_methods(self):
        for method in ("bm25", "dense", "hybrid"):
            got = self.retriever.search("pipe read hangs write end open", "PI01", "Debug", method)
            self.assertIn("Troubleshooting", [r["section_type"] for r in got[:3]])
            self.assertIn("semantic_score", got[0])


class BehaviourTests(unittest.TestCase):
    def test_trace_normalization(self):
        trace = "1234 12:02:01 fork() = 44\n44 write(1, \"x\", 1) = 1\n1234 wait4(44, NULL, 0, NULL) = 44\n"
        self.assertEqual(normalize_trace(trace), ["PROCESS_CREATE", "WRITE", "PARENT_WAIT"])

    def test_static_features(self):
        cases = {r["id"]: r for r in build_cases()}
        self.assertTrue(cases["baseline"]["features"]["parent_wait_present"])
        self.assertFalse(cases["missing_wait_a"]["features"]["wait_present"])
        self.assertTrue(cases["wait_in_child_a"]["features"]["wait_in_child_branch"])

    def test_missing_wait_diagnosis(self):
        cases = build_cases()
        sample = next(r for r in cases if r["id"] == "missing_wait_a")
        result = diagnose(sample["source_code"], "parent complete\nchild finished", "FW01", Retriever(load_demo()), cases, "Why first parent?")
        self.assertEqual(result["failure_label"], "missing_wait")
        self.assertEqual(result["execution_status"], "not_executed_static_analysis_only")
        self.assertTrue(result["retrieved_sources"])


if __name__ == "__main__":
    unittest.main()
