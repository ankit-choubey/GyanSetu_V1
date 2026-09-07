"""
Seed Content Ingestion Pipeline

Processes public PDF seed documents from:
    ml_pipeline/seed_content/raw/

Outputs structured JSON files to:
    ml_pipeline/seed_content/processed/

Updates:
    ml_pipeline/seed_content/manifest.json

Uses the existing document_processor.py so the seed-content
pipeline remains consistent with the rest of the ML pipeline.
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

# Allow this file to work when executed as:
#   python -m ml_pipeline.ingest_seed_content
# from the repository root.
from ml_pipeline.document_processor import process_document_structured


BASE_DIR = Path(__file__).resolve().parent
SEED_DIR = BASE_DIR / "seed_content"
RAW_DIR = SEED_DIR / "raw"
PROCESSED_DIR = SEED_DIR / "processed"
MANIFEST_PATH = SEED_DIR / "manifest.json"


def load_manifest() -> dict:
    """Load the seed-content manifest, creating it if necessary."""
    if not MANIFEST_PATH.exists():
        return {"documents": []}

    try:
        with MANIFEST_PATH.open("r", encoding="utf-8") as f:
            data = json.load(f)

        if not isinstance(data, dict):
            raise ValueError("Manifest must contain a JSON object.")

        if "documents" not in data:
            data["documents"] = []

        if not isinstance(data["documents"], list):
            raise ValueError("'documents' must be a JSON list.")

        return data

    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Invalid JSON in manifest: {MANIFEST_PATH}"
        ) from exc


def save_manifest(manifest: dict) -> None:
    """Write the manifest using readable UTF-8 JSON."""
    with MANIFEST_PATH.open("w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
        f.write("\n")


def make_document_id(pdf_path: Path) -> str:
    """Create a stable document ID from the filename."""
    return pdf_path.stem.lower().replace(" ", "_")


def existing_document_ids(manifest: dict) -> set[str]:
    """Return document IDs already recorded in the manifest."""
    return {
        str(doc.get("document_id"))
        for doc in manifest.get("documents", [])
        if doc.get("document_id")
    }


def build_processed_record(
    pdf_path: Path,
    document_id: str,
    pages: list[dict],
) -> dict:
    """Build the JSON representation saved for a processed document."""

    total_characters = sum(
        len(page.get("text", ""))
        for page in pages
    )

    ocr_pages = sum(
        1
        for page in pages
        if page.get("ocr_used") is True
    )

    table_pages = sum(
        1
        for page in pages
        if page.get("tables")
    )

    return {
        "document_id": document_id,
        "filename": pdf_path.name,
        "source_file": str(pdf_path.relative_to(BASE_DIR.parent)),
        "processed_at": datetime.now(timezone.utc).isoformat(),
        "page_count": len(pages),
        "total_characters": total_characters,
        "ocr_pages": ocr_pages,
        "table_pages": table_pages,
        "pages": pages,
    }


def build_manifest_entry(
    pdf_path: Path,
    document_id: str,
    processed_record: dict,
) -> dict:
    """Build metadata for the manifest."""

    return {
        "document_id": document_id,
        "filename": pdf_path.name,
        "title": pdf_path.stem.replace("_", " ").strip(),
        "source": "Public statistical source",
        "source_url": "",
        "topic": "Official statistics and statistical methodology",
        "license_or_access_note": (
            "Publicly accessible source document. "
            "Verify source-specific reuse terms before redistribution."
        ),
        "processed_file": (
            f"ml_pipeline/seed_content/processed/"
            f"{document_id}.json"
        ),
        "page_count": processed_record["page_count"],
        "total_characters": processed_record["total_characters"],
        "ocr_pages": processed_record["ocr_pages"],
        "table_pages": processed_record["table_pages"],
        "status": "processed",
    }


def process_pdf(
    pdf_path: Path,
    manifest: dict,
) -> bool:
    """Process one PDF and update the manifest."""

    document_id = make_document_id(pdf_path)
    output_path = PROCESSED_DIR / f"{document_id}.json"

    print()
    print("=" * 70)
    print(f"Processing: {pdf_path.name}")
    print(f"Document ID: {document_id}")
    print("=" * 70)

    try:
        print("Extracting pages...")

        pages = process_document_structured(str(pdf_path))

        print(f"Extracted pages: {len(pages)}")

        total_characters = sum(
            len(page.get("text", ""))
            for page in pages
        )

        ocr_pages = sum(
            1
            for page in pages
            if page.get("ocr_used") is True
        )

        table_pages = sum(
            1
            for page in pages
            if page.get("tables")
        )

        print(f"Characters: {total_characters}")
        print(f"OCR pages: {ocr_pages}")
        print(f"Table pages: {table_pages}")

        record = build_processed_record(
            pdf_path,
            document_id,
            pages,
        )

        with output_path.open("w", encoding="utf-8") as f:
            json.dump(
                record,
                f,
                indent=2,
                ensure_ascii=False,
            )
            f.write("\n")

        print(f"Saved: {output_path}")

        # Remove an older manifest entry for this document if one exists.
        manifest["documents"] = [
            doc
            for doc in manifest["documents"]
            if doc.get("document_id") != document_id
        ]

        manifest["documents"].append(
            build_manifest_entry(
                pdf_path,
                document_id,
                record,
            )
        )

        save_manifest(manifest)

        print("Manifest updated.")
        print("STATUS: SUCCESS")

        return True

    except Exception as exc:
        print(f"ERROR: {type(exc).__name__}: {exc}")
        print("STATUS: FAILED")
        return False


def main() -> int:
    """Run seed-content ingestion."""

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    manifest = load_manifest()

    pdf_files = sorted(
        RAW_DIR.glob("*.pdf"),
        key=lambda path: path.name.lower(),
    )

    if not pdf_files:
        print(f"No PDF files found in: {RAW_DIR}")
        return 0

    print("=" * 70)
    print("GYANSETU SEED CONTENT INGESTION")
    print("=" * 70)
    print(f"PDFs found: {len(pdf_files)}")
    print(f"Raw directory: {RAW_DIR}")
    print(f"Processed directory: {PROCESSED_DIR}")

    success_count = 0
    failure_count = 0

    for pdf_path in pdf_files:
        document_id = make_document_id(pdf_path)
        output_path = PROCESSED_DIR / f"{document_id}.json"

        # Skip only when both the processed file and manifest entry exist.
        if (
            output_path.exists()
            and document_id in existing_document_ids(manifest)
        ):
            print()
            print(f"SKIPPING already processed: {pdf_path.name}")
            continue

        if process_pdf(pdf_path, manifest):
            success_count += 1
        else:
            failure_count += 1

    print()
    print("=" * 70)
    print("INGESTION SUMMARY")
    print("=" * 70)
    print(f"PDFs found: {len(pdf_files)}")
    print(f"Successfully processed: {success_count}")
    print(f"Failed: {failure_count}")
    print(f"Manifest: {MANIFEST_PATH}")
    print("=" * 70)

    return 1 if failure_count else 0


if __name__ == "__main__":
    sys.exit(main())