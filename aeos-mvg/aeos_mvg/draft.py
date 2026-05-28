"""W1 step ①②: draft a single reply offline. No LINE, no DB.

    poetry run python -m aeos_mvg.draft "你們週末有出貨嗎？"
    poetry run python -m aeos_mvg.draft --knowledge data/knowledge.md "退貨要幾天？"
"""

from __future__ import annotations

import argparse

from .knowledge import load_knowledge
from .llm import generate_draft


def main() -> None:
    parser = argparse.ArgumentParser(description="對單一客戶問題產生草稿回覆")
    parser.add_argument("question", help="客戶問題")
    parser.add_argument("--knowledge", default="data/knowledge.md", help="知識檔路徑")
    args = parser.parse_args()

    knowledge = load_knowledge(args.knowledge)
    result = generate_draft(args.question, knowledge)

    print(result.text)
    print("\n---")
    print(f"needs_human: {result.needs_human}")
    u = result.usage
    print(
        f"tokens  in={u.input_tokens}  out={u.output_tokens}  "
        f"cache_write={getattr(u, 'cache_creation_input_tokens', 0)}  "
        f"cache_read={getattr(u, 'cache_read_input_tokens', 0)}"
    )


if __name__ == "__main__":
    main()
