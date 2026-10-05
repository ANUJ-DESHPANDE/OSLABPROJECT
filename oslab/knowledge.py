import hashlib
import json
import math
import re
from collections import Counter
from pathlib import Path

from sklearn.decomposition import TruncatedSVD
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

SECTIONS = {"Aim", "Theory", "Setup", "Procedure", "Algorithm", "Program", "Expected Output", "Troubleshooting", "Viva"}
TOKEN = re.compile(r"[a-z][a-z0-9_]*", re.I)


def tokens(text):
    return TOKEN.findall(text.lower())


def parse_markdown(path):
    """Retain experiment headings and logical sections; split only oversized sections."""
    source = Path(path)
    title, experiment_id, section, lines = "", "", None, []
    records = []

    def flush():
        body = "\n".join(lines).strip()
        if not section or not body:
            return
        words = body.split()
        chunks = [" ".join(words[i:i + 350]) for i in range(0, len(words), 350)]
        for part, chunk in enumerate(chunks, 1):
            digest = hashlib.sha256(chunk.encode()).hexdigest()
            records.append({"id": f"{experiment_id}:{section.lower().replace(' ', '_')}:{part}",
                            "experiment_id": experiment_id, "experiment_name": title,
                            "topic": title.split(":", 1)[-1].strip(), "section_type": section,
                            "source": source.name, "page_section": f"{section} #{part}",
                            "language": "C" if section == "Program" else "en",
                            "content_hash": digest, "text": chunk})

    for line in source.read_text(encoding="utf-8").splitlines():
        if line.startswith("# "):
            flush()
            match = re.match(r"# Experiment ([A-Z0-9]+): (.+)", line)
            if not match:
                raise ValueError(f"Invalid experiment heading in {source}")
            experiment_id, title = match.groups()
            section, lines = None, []
        elif line.startswith("## "):
            flush()
            section = line[3:].strip()
            if section not in SECTIONS:
                raise ValueError(f"Unknown section {section} in {source}")
            lines = []
        elif section:
            lines.append(line)
    flush()
    return records


def ingest(paths):
    records, seen = [], set()
    for path in sorted(map(Path, paths)):
        for record in parse_markdown(path):
            key = (record["experiment_id"], record["section_type"], record["content_hash"])
            if key not in seen:
                seen.add(key)
                records.append(record)
    return records


class Retriever:
    def __init__(self, records):
        self.records = records
        self.docs = [tokens(r["text"] + " " + r["section_type"] + " " + r["topic"]) for r in records]
        self.df = Counter(t for doc in self.docs for t in set(doc))
        self.avgdl = sum(map(len, self.docs)) / max(1, len(self.docs))
        texts = [r["text"] + " " + r["section_type"] + " " + r["topic"] for r in records]
        self.vectorizer = TfidfVectorizer(ngram_range=(1, 2), stop_words="english", sublinear_tf=True)
        matrix = self.vectorizer.fit_transform(texts)
        # LSA gives a compact dense latent-space representation, with no model download.
        components = min(24, matrix.shape[0] - 1, matrix.shape[1] - 1)
        self.svd = TruncatedSVD(n_components=components, random_state=7) if components >= 2 else None
        self.dense = self.svd.fit_transform(matrix) if self.svd else matrix.toarray()

    def search(self, query, experiment=None, mode="Debug", method="hybrid", k=5):
        qtokens = tokens(query)
        n = len(self.docs)
        lexical = []
        for doc in self.docs:
            count = Counter(doc)
            score = sum(math.log(1 + (n - self.df[t] + .5) / (self.df[t] + .5)) *
                        count[t] * 2.2 / (count[t] + 1.2 * (.25 + .75 * len(doc) / self.avgdl))
                        for t in set(qtokens) if count[t])
            lexical.append(score)
        qvec = self.vectorizer.transform([query])
        dense_q = self.svd.transform(qvec) if self.svd else qvec.toarray()
        semantic = cosine_similarity(dense_q, self.dense)[0].tolist()
        eligible = [i for i, r in enumerate(self.records) if not experiment or r["experiment_id"] == experiment]
        if not eligible:
            return []
        lex_order = sorted(eligible, key=lambda i: (-lexical[i], i))
        sem_order = sorted(eligible, key=lambda i: (-semantic[i], i))
        lr = {idx: rank + 1 for rank, idx in enumerate(lex_order)}
        sr = {idx: rank + 1 for rank, idx in enumerate(sem_order)}
        preferred = {"Debug": {"Troubleshooting", "Program", "Expected Output"},
                     "Viva": {"Viva", "Theory", "Algorithm"},
                     "Procedure": {"Procedure", "Program"},
                     "Learn": {"Aim", "Theory"}}.get(mode, set())
        output = []
        for i in eligible:
            fused = 1 / (60 + lr[i]) + 1 / (60 + sr[i])
            bonus = .001 if self.records[i]["section_type"] in preferred else 0
            score = {"bm25": lexical[i], "dense": semantic[i], "hybrid": fused + bonus}[method]
            output.append({**self.records[i], "lexical_score": round(lexical[i], 5),
                           "semantic_score": round(semantic[i], 5), "fused_score": round(fused + bonus, 5),
                           "score": float(score)})
        return sorted(output, key=lambda r: (-r["score"], r["id"]))[:k]


def save_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def load_demo():
    return ingest(Path("data/demo").glob("*.md"))
