"""Command-line entry point and localhost HTTP routes for the browser UI."""

import argparse
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from .behaviour import save_cases
from .diagnose import diagnose
from .evaluate import run
from .knowledge import Retriever, load_demo, save_json
from .concepts import load_concepts
from .process_model import grade_prediction, scenario
from .studio import save_audit
from .scheduling import simulate
from .course import CourseSearch, REFERENCE_INDEX_PATH, import_course
from .code_review import inspect_code, pipe_eof_walkthrough, retrieval_query
from .local_model import explain, status as model_status
from .visuals import choose_visual


def build():
    """Refresh the small public demo records and audit; private indexes stay local."""
    records = load_demo()
    save_json("data/processed/knowledge.json", records)
    cases = save_cases()
    save_json("results/demo_knowledge.json", records)
    save_json("results/demo_behaviour.json", cases)
    save_audit()
    return records, cases


def serve(port):
    """Load local datasets once, then serve UI files and narrow JSON endpoints."""
    # Browser assets are read once at startup; restarting picks up UI edits.
    records, cases = build()
    retriever = Retriever(records)
    page = Path("web/index.html").read_bytes()
    stylesheet = Path("web/app.css").read_bytes()
    schedule_stylesheet = Path("web/schedule.css").read_bytes()
    course_stylesheet = Path("web/course.css").read_bytes()
    script = Path("web/app.js").read_bytes()
    studio = save_audit()
    concepts = load_concepts()
    course = CourseSearch.load(include_demo=True, reference_index_path=REFERENCE_INDEX_PATH)

    class Handler(BaseHTTPRequestHandler):
        """Route requests; no route runs pasted student code."""
        def do_GET(self):
            # GET returns the website, data audits and status of local services.
            parsed = urlparse(self.path)
            route = parsed.path
            if route == "/":
                body, kind = page, "text/html; charset=utf-8"
            elif route == "/app.css":
                body, kind = stylesheet, "text/css; charset=utf-8"
            elif route == "/schedule.css":
                body, kind = schedule_stylesheet, "text/css; charset=utf-8"
            elif route == "/course.css":
                body, kind = course_stylesheet, "text/css; charset=utf-8"
            elif route == "/app.js":
                body, kind = script, "text/javascript; charset=utf-8"
            elif route == "/api/records":
                body, kind = json.dumps(records).encode(), "application/json"
            elif route == "/api/cases":
                body, kind = json.dumps(cases).encode(), "application/json"
            elif route == "/api/studio":
                body, kind = json.dumps(studio).encode(), "application/json"
            elif route == "/api/concepts":
                body, kind = json.dumps(concepts).encode(), "application/json"
            elif route == "/api/course/status":
                body, kind = json.dumps(course.status() if course else {"ready": False}).encode(), "application/json"
            elif route == "/api/model/status":
                body, kind = json.dumps(model_status()).encode(), "application/json"
            elif route == "/api/metrics":
                body, kind = json.dumps({"processing": json.loads(Path("results/processing_metrics.json").read_text(encoding="utf-8")),
                                          "retrieval": json.loads(Path("results/retrieval_metrics.json").read_text(encoding="utf-8")),
                                          "diagnostic": json.loads(Path("results/diagnostic_metrics.json").read_text(encoding="utf-8"))}).encode(), "application/json"
            elif route == "/api/process":
                params = parse_qs(parsed.query)
                wait_value = params.get("wait", ["1"])[0]
                schedule = params.get("schedule", ["parent_first"])[0]
                if wait_value not in {"0", "1"} or schedule not in {"parent_first", "child_first"}:
                    self.send_error(400)
                    return
                body, kind = json.dumps(scenario(wait_value == "1", schedule)).encode(), "application/json"
            else:
                self.send_error(404)
                return
            self.send_response(200)
            self.send_header("Content-Type", kind)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_POST(self):
            # POST validates bounded JSON before delegating to a specific tool.
            if self.path not in {"/api/analyse", "/api/practice", "/api/schedule", "/api/course/search", "/api/course/ask", "/api/code/review"}:
                self.send_error(404)
                return
            try:
                length = int(self.headers.get("Content-Length", "0"))
                if length < 0 or length > 100_000:
                    raise ValueError("Input too large")
                data = json.loads(self.rfile.read(length))
                if not isinstance(data, dict):
                    raise ValueError("Request body must be a JSON object")
                if self.path in {"/api/course/search", "/api/course/ask"}:
                    # Search returns original passages. /ask additionally asks the local
                    # model to explain at most four of them with checked source IDs.
                    question = str(data.get("question", "")).strip()[:500]
                    if not question:
                        raise ValueError("Enter a question or search phrase")
                    method = str(data.get("method", "hybrid"))
                    scope = str(data.get("scope", "course"))
                    matches = course.search(question, method=method, scope=scope) if course else []
                    result = {"matches": matches,
                              "ready": course is not None, "method": method, "scope": scope}
                    if self.path == "/api/course/ask" and matches:
                        try:
                            hint = choose_visual(question, matches)
                            result["topic"] = hint["id"] if hint else None
                            result["explanation"] = explain(question, matches[:4],
                                                            topic_hint=hint["title"] if hint else None)
                            result["visual"] = result["explanation"]["visual"]
                        except RuntimeError as error:
                            result["model_error"] = str(error)
                elif self.path == "/api/code/review":
                    # This path only inspects pasted text. It cannot compile or run it.
                    raw_code = str(data.get("code", ""))
                    code = raw_code[:20000]
                    question = str(data.get("question", "")).strip()[:500]
                    observed = str(data.get("output", ""))[:3000]
                    if not code.strip():
                        raise ValueError("Paste code to review")
                    inspection = inspect_code(code)
                    query = retrieval_query(question, inspection)
                    candidates = course.search(query, limit=10) if course and query else []
                    sources = [item for item in candidates if not item["location"].startswith("Viva")][:4]
                    result = {"inspection": inspection, "sources": sources,
                              "model_input_truncated": len(code) > 6000,
                              "analysis_input_truncated": len(raw_code) > 20000,
                              "user_supplied_output": bool(observed)}
                    if sources:
                        hint = choose_visual(question, sources, inspection["topics"])
                        result["topic"] = hint["id"] if hint else None
                        checked = pipe_eof_walkthrough(code, inspection, sources)
                        if checked:
                            result["explanation"] = checked
                            result["visual"] = checked["visual"]
                        else:
                            try:
                                result["explanation"] = explain(question or "Review this OS lab code", sources,
                                                                code=code, observations=observed,
                                                                inspection=inspection,
                                                                topic_hint=hint["title"] if hint else None)
                                result["visual"] = result["explanation"]["visual"]
                            except RuntimeError as error:
                                result["model_error"] = str(error)
                elif self.path == "/api/schedule":
                    # Numeric timelines come from deterministic Python, not the LLM.
                    result = simulate(data.get("processes"), data.get("algorithm", "FCFS"), data.get("quantum", 2))
                elif self.path == "/api/practice":
                    use_wait = data.get("use_wait")
                    if not isinstance(use_wait, bool):
                        raise ValueError("use_wait must be boolean")
                    result = grade_prediction(use_wait, data.get("schedule", "parent_first"),
                                              data.get("step"), data.get("answer"))
                else:
                    experiment = data.get("experiment", "FW01")
                    mode = data.get("mode", "Debug")
                    if experiment not in {"FW01", "EX01", "PI01"} or mode not in {"Learn", "Procedure", "Debug", "Viva"}:
                        raise ValueError("Invalid experiment or mode")
                    question = str(data.get("question", ""))[:3000]
                    if mode == "Debug":
                        result = diagnose(str(data.get("code", ""))[:50000], str(data.get("output", ""))[:10000], experiment, retriever, cases, question)
                        result["course_sources"] = course.search("fork waitpid parent child", limit=2) if course and experiment == "FW01" else []
                    else:
                        sources = retriever.search(question, experiment, mode, k=5)
                        result = {"likely_issue": None, "retrieved_sources": sources,
                                  "explanation": "Relevant source sections are listed below. No diagnosis is produced outside Debug mode.",
                                  "execution_status": "not_requested"}
                body = json.dumps(result).encode()
                self.send_response(200)
            except (ValueError, json.JSONDecodeError) as error:
                body = json.dumps({"error": str(error)}).encode()
                self.send_response(400)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    print(f"OS Lab Companion: http://127.0.0.1:{port}")
    server.serve_forever()


def main():
    """Expose import, build, evaluate and serve commands from one entry point."""
    parser = argparse.ArgumentParser(description="OS Lab Companion local demo")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("build")
    sub.add_parser("evaluate")
    sub.add_parser("collect-trusted")
    imported = sub.add_parser("import-course")
    imported.add_argument("zip_path", help="local ZIP of course PDFs, PPTX and DOCX files")
    reference = sub.add_parser("import-reference")
    reference.add_argument("zip_path", help="local ZIP of textbook PDF and publisher companion slides")
    inspect = sub.add_parser("inspect")
    inspect.add_argument("dataset", choices=["knowledge", "behaviour"])
    web = sub.add_parser("serve")
    web.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    if args.command == "build":
        records, cases = build()
        print(f"Built {len(records)} knowledge records and {len(cases)} behaviour cases")
    elif args.command == "evaluate":
        print(json.dumps(run(), indent=2))
    elif args.command == "collect-trusted":
        from .collect import collect_trusted
        cases = collect_trusted()
        print(f"Collected trusted execution evidence for {len(cases)} cases")
    elif args.command == "import-course":
        payload = import_course(args.zip_path)
        print(f"Indexed {len(payload['documents'])} documents into {len(payload['records'])} passages; "
              f"skipped {len(payload['skipped'])} files. Private index: data/private/processed/course_index.json")
    elif args.command == "import-reference":
        payload = import_course(args.zip_path, REFERENCE_INDEX_PATH, max_entry_size=35_000_000)
        print(f"Indexed {len(payload['documents'])} textbook resource files into {len(payload['records'])} passages; "
              f"skipped {len(payload['skipped'])} files. Private index: {REFERENCE_INDEX_PATH}")
    elif args.command == "inspect":
        build()
        print(Path(f"data/processed/{args.dataset}.json").read_text(encoding="utf-8"))
    else:
        serve(args.port)


if __name__ == "__main__":
    main()
