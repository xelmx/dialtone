"""dialtone command line."""

from __future__ import annotations

import argparse
from pathlib import Path

DEFAULT_MODEL = "openai/whisper-large-v3-turbo"


def main(argv: list[str] | None = None) -> None:
    import sys

    # Windows consoles default to cp1252, which cannot print the en dashes and
    # arrows in the tables. Everything this tool writes is UTF-8.
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")

    ap = argparse.ArgumentParser(prog="dialtone", description=__doc__)
    ap.add_argument("--data-dir", type=Path, default=Path("data"))
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("fetch", help="download and extract LibriSpeech test-clean")

    m = sub.add_parser("manifest", help="pin a seeded subset of utterance ids")
    m.add_argument("-n", type=int, default=200)
    m.add_argument("--seed", type=int, default=42)
    m.add_argument("-o", "--out", type=Path, default=None)

    l = sub.add_parser("listen", help="write clean/degraded WAV pairs so you can hear the chain")
    l.add_argument("manifest", type=Path)
    l.add_argument("-k", type=int, default=5)
    l.add_argument("--out", type=Path, default=Path("listen"))
    l.add_argument("--conditions", default="clean,g711u,pots")

    r = sub.add_parser("run", help="transcribe the manifest under each condition (resumable)")
    r.add_argument("manifest", type=Path)
    r.add_argument("--model", default=DEFAULT_MODEL, help="HF hub id or local path; adapter picked from config.json")
    r.add_argument("--conditions", default="clean,g711u,pots")
    r.add_argument("--out", type=Path, required=True)
    r.add_argument("--batch-size", type=int, default=16, help="max utterances per batch")
    r.add_argument("--max-batch-seconds", type=float, default=160.0, help="max total audio per batch")
    r.add_argument("--dtype", choices=["auto", "fp16", "bf16", "fp32"], default="auto", help="auto = per model card")
    r.add_argument("--device", default=None, help="e.g. cuda:0 or cpu; default auto")
    r.add_argument("--limit", type=int, default=None, help="only the first N manifest ids (smoke tests)")

    p = sub.add_parser("report", help="score one results directory")
    p.add_argument("out", type=Path)
    p.add_argument("--normalizer", choices=["basic", "whisper_en"], default="whisper_en")

    c = sub.add_parser("compare", help="one table across several results directories")
    c.add_argument("dirs", type=Path, nargs="+")
    c.add_argument("--normalizer", choices=["basic", "whisper_en"], default="whisper_en")
    c.add_argument("--out", type=Path, default=None, help="default results/compare.<normalizer>.md")

    i = sub.add_parser("inspect", help="which utterances moved under degradation, and the shared-error floor")
    i.add_argument("dirs", type=Path, nargs="+")
    i.add_argument("--normalizer", choices=["basic", "whisper_en"], default="whisper_en")
    i.add_argument("--condition", default=None, help="condition to list right→wrong examples for (default: worst)")
    i.add_argument("-k", type=int, default=8)
    i.add_argument("--out", type=Path, default=None, help="also write markdown here")

    al = sub.add_parser("align", help="forced-align reference words to the clean audio (cached, resumable)")
    al.add_argument("manifest", type=Path)
    al.add_argument("--model", default="Qwen/Qwen3-ForcedAligner-0.6B-hf")
    al.add_argument("--out", type=Path, default=Path("data/alignments"))
    al.add_argument("--dtype", choices=["auto", "fp16", "bf16", "fp32"], default="auto")
    al.add_argument("--device", default=None)
    al.add_argument("--limit", type=int, default=None)
    al.add_argument("--print", dest="show", type=int, default=0, help="print word times for the first N (eyeball the aligner)")

    st = sub.add_parser("stream", help="transcribe growing prefixes of each utterance (resumable)")
    st.add_argument("manifest", type=Path)
    st.add_argument("--model", default=DEFAULT_MODEL)
    st.add_argument("--conditions", default="clean,pots_babble10")
    st.add_argument("--out", type=Path, required=True)
    st.add_argument("--first", type=float, default=1.0, help="first prefix length, s")
    st.add_argument("--step", type=float, default=0.5, help="prefix step, s")
    st.add_argument("--batch-size", type=int, default=16)
    st.add_argument("--max-batch-seconds", type=float, default=160.0)
    st.add_argument("--dtype", choices=["auto", "fp16", "bf16", "fp32"], default="auto")
    st.add_argument("--device", default=None)
    st.add_argument("--limit", type=int, default=None)

    se = sub.add_parser("settle", help="settle metrics for one or more stream result directories")
    se.add_argument("dirs", type=Path, nargs="+")
    se.add_argument("--alignments", type=Path, default=Path("data/alignments/qwen3-forced-aligner-0.6b.jsonl"))
    se.add_argument("--normalizer", choices=["basic", "whisper_en"], default="whisper_en")
    se.add_argument("--out", type=Path, default=None, help="default results/stream/settle.<normalizer>.md")

    a = ap.parse_args(argv)

    if a.cmd == "fetch":
        from . import data

        root = data.fetch(a.data_dir)
        print(f"ready: {root} ({len(data.index(root))} utterances)")

    elif a.cmd == "manifest":
        from . import data

        utts = data.index(data.fetch(a.data_dir))
        out = a.out or Path("manifests") / f"librispeech-test-clean-{a.n}.txt"
        ids = data.make_manifest(utts, a.n, a.seed, out)
        spk = len({utts[i]["speaker"] for i in ids})
        print(f"wrote {out}: {len(ids)} utterances from {spk} speakers (seed {a.seed})")

    elif a.cmd == "listen":
        import soundfile as sf

        from . import data, degrade

        utts = data.index(data.fetch(a.data_dir))
        ids = data.read_manifest(a.manifest)[: a.k]
        conds = a.conditions.split(",")
        pool = degrade.BabblePool.from_index(utts) if degrade.needs_pool(conds) else None
        a.out.mkdir(parents=True, exist_ok=True)
        for i in ids:
            x = data.load_audio(utts[i]["path"])
            ctx = degrade.Context(pool=pool, speaker=utts[i]["speaker"])
            for cond in conds:
                sf.write(a.out / f"{i}.{cond}.wav", degrade.apply(x, cond, ctx), data.SR, subtype="PCM_16")
            print(f"{i}: {utts[i]['text']}")
        print(f"wrote {len(ids)} x {a.conditions} to {a.out}/")

    elif a.cmd == "run":
        from . import run

        run.run(
            model=a.model,
            manifest=a.manifest,
            conditions=a.conditions.split(","),
            out=a.out,
            data_dir=a.data_dir,
            batch_size=a.batch_size,
            max_batch_seconds=a.max_batch_seconds,
            dtype=a.dtype,
            device=a.device,
            limit=a.limit,
        )

    elif a.cmd == "report":
        from . import report

        print(report.as_markdown(report.summarize(a.out, normalizer=a.normalizer)))

    elif a.cmd == "compare":
        from . import report

        _, md = report.compare(a.dirs, normalizer=a.normalizer)
        out = a.out or Path("results") / f"compare.{a.normalizer}.md"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(md, encoding="utf-8", newline="\n")
        print(md)
        print(f"wrote {out}")

    elif a.cmd == "inspect":
        from . import inspect as insp

        md = insp.report(a.dirs, normalizer=a.normalizer, worst=a.condition, k=a.k)
        if a.out:
            a.out.parent.mkdir(parents=True, exist_ok=True)
            a.out.write_text(md, encoding="utf-8", newline="\n")
        print(md)

    elif a.cmd == "align":
        from . import align

        align.build(a.manifest, a.data_dir, out=a.out, model=a.model, dtype=a.dtype, device=a.device, limit=a.limit, show=a.show)

    elif a.cmd == "stream":
        from . import stream

        stream.run(
            model=a.model,
            manifest=a.manifest,
            conditions=a.conditions.split(","),
            out=a.out,
            data_dir=a.data_dir,
            first=a.first,
            step=a.step,
            batch_size=a.batch_size,
            max_batch_seconds=a.max_batch_seconds,
            dtype=a.dtype,
            device=a.device,
            limit=a.limit,
        )

    elif a.cmd == "settle":
        from . import settle

        _, md = settle.compare(a.dirs, a.alignments, normalizer=a.normalizer)
        out = a.out or Path("results") / "stream" / f"settle.{a.normalizer}.md"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(md, encoding="utf-8", newline="\n")
        print(md)
        print(f"wrote {out}")
