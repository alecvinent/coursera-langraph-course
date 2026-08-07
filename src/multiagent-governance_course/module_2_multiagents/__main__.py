from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from module_2_multiagents.runtime import run_pipeline  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="module_2_multiagents",
        description="Run the Researcher -> Writer -> SEO Analyst blog pipeline.",
    )
    parser.add_argument("topic", help="The blog post topic to seed the chain")
    args = parser.parse_args(argv)

    try:
        state = run_pipeline(args.topic)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2

    print("=== Research Outline ===")
    print(state.outline)
    print("\n=== Article Draft ===")
    print(state.draft)
    print("\n=== SEO Feedback ===")
    print(state.seo_feedback)
    print(f"\n[processing_outcome={state.processing_outcome}]")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())