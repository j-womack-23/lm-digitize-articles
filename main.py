"""CLI entrypoint: convert a PDF magazine article to a WordPress HTML file."""

import argparse
import sys

from extract import extract_text
from parse import parse_article
from generate import write_output


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Convert a PDF magazine article to a WP Bakery-ready HTML file."
    )
    parser.add_argument("pdf", help="Path to the input PDF file")
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Print extracted text and parsed JSON before generating HTML",
    )
    args = parser.parse_args()

    print(f"Extracting text from {args.pdf} ...")
    raw_text = extract_text(args.pdf)

    if args.debug:
        print("\n--- EXTRACTED TEXT ---")
        print(raw_text[:3000])
        print("...")

    print("Parsing article structure with Claude ...")
    article = parse_article(raw_text)

    if args.debug:
        import json
        print("\n--- PARSED STRUCTURE ---")
        print(json.dumps(article, indent=2))

    print("Generating HTML ...")
    out_path = write_output(article, args.pdf)

    print(f"\nDone. Output written to: {out_path}")


if __name__ == "__main__":
    main()
