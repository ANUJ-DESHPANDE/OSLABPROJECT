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


def build():
    records = load_demo()
    save_json("data/processed/knowledge.json", records)
    cases = save_cases()
    save_json("results/demo_knowledge.json", records)
    save_json("results/demo_behaviour.json", cases)
    save_audit()
    return records, cases


def serve(port):
    records, cases = build()
    retriever = Retriever(records)
    page = Path("web/index.html").read_bytes()
    stylesheet = Path("web/app.css").read_bytes()
    schedule_stylesheet = Path("web/schedule.css").read_bytes()
    script = Path("web/app.js").read_bytes()
    studio = save_audit()
    concepts = load_concepts()

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            parsed = urlparse(self.path)
            route = parsed.path
            if route == "/":
                body, kind = page, "text/html; charset=utf-8"
            elif route == "/app.css":
                body, kind = stylesheet, "text/css; charset=utf-8"
            elif route == "/schedule.css":
                body, kind = schedule_stylesheet, "text/css; charset=utf-8"
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
            if self.path not in {"/api/analyse", "/api/practice", "/api/schedule"}:
                self.send_error(404)
                return
            try:
                length = int(self.headers.get("Content-Length", "0"))
                if length < 0 or length > 100_000:
                    raise ValueError("Input too large")
                data = json.loads(self.rfile.read(length))
                if not isinstance(data, dict):
                    raise ValueError("Request body must be a JSON object")
                if self.path == "/api/schedule":
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
    print(f"OSLab Copilot: http://127.0.0.1:{port}")
    server.serve_forever()


def main():
    parser = argparse.ArgumentParser(description="OSLab Copilot local demo")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("build")
    sub.add_parser("evaluate")
    sub.add_parser("collect-trusted")
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
    elif args.command == "inspect":
        build()
        print(Path(f"data/processed/{args.dataset}.json").read_text(encoding="utf-8"))
    else:
        serve(args.port)


if __name__ == "__main__":
    main()
