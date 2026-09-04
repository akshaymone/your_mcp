#!/usr/bin/env python3
"""
backfill_file_paths.py
======================
One-time migration script that:
  1. Scrolls all points in the Qdrant 'vision_pages' collection.
  2. For each point where 'file_path' is null or the path no longer exists,
     decodes 'image_base64' from the payload and writes a JPEG to a stable
     persistent directory: ~/.ask_me_store/vision_pages/<doc_name>/page_NNN.jpg
  3. Patches the Qdrant point payload in-place with the new 'file_path'.

No re-embedding is done — vectors are untouched.
This only needs to be run ONCE to fix existing docs.

Usage:
    python backfill_file_paths.py [--host 127.0.0.1] [--port 6333] \
                                  [--collection vision_pages] \
                                  [--store-dir ~/.ask_me_store/vision_pages] \
                                  [--dry-run]
"""

import argparse
import base64
import logging
import os
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


def backfill(host: str, port: int, collection: str, store_dir: Path, dry_run: bool):
    from qdrant_client import QdrantClient

    qdrant = QdrantClient(host=host, port=port, timeout=30.0)

    if not qdrant.collection_exists(collection):
        logger.error(f"Collection '{collection}' does not exist. Aborting.")
        return

    logger.info(f"Scrolling collection '{collection}' ...")

    total_scanned = 0
    total_patched = 0
    total_skipped = 0
    offset = None

    while True:
        batch, next_offset = qdrant.scroll(
            collection_name=collection,
            limit=50,
            offset=offset,
            with_payload=True,
            with_vectors=False,
        )

        if not batch:
            break

        for point in batch:
            total_scanned += 1
            payload = point.payload or {}
            doc_name = payload.get("doc_name", "unknown")
            page_num = payload.get("page_number", 0)
            existing_path = payload.get("file_path")

            # ── Check if file_path is already valid ───────────────────────────
            if existing_path and Path(existing_path).exists():
                logger.debug(f"  [{doc_name} p{page_num}] file_path already valid → skip")
                total_skipped += 1
                continue

            # ── Decode base64 and write JPEG ──────────────────────────────────
            img_b64 = payload.get("image_base64", "")
            if not img_b64:
                logger.warning(f"  [{doc_name} p{page_num}] No image_base64 in payload — cannot backfill.")
                total_skipped += 1
                continue

            doc_dir = store_dir / doc_name
            if not dry_run:
                doc_dir.mkdir(parents=True, exist_ok=True)

            img_file = doc_dir / f"page_{page_num:03d}.jpg"

            if not dry_run:
                try:
                    img_data = base64.b64decode(img_b64)
                    img_file.write_bytes(img_data)
                    logger.info(f"  [{doc_name} p{page_num}] Wrote JPEG → {img_file}")
                except Exception as e:
                    logger.error(f"  [{doc_name} p{page_num}] Failed to decode/write image: {e}")
                    total_skipped += 1
                    continue

                # ── Patch Qdrant payload ──────────────────────────────────────
                try:
                    qdrant.set_payload(
                        collection_name=collection,
                        payload={"file_path": str(img_file)},
                        points=[point.id],
                    )
                    logger.info(f"  [{doc_name} p{page_num}] Patched Qdrant payload with file_path.")
                    total_patched += 1
                except Exception as e:
                    logger.error(f"  [{doc_name} p{page_num}] Failed to patch Qdrant: {e}")
                    total_skipped += 1
            else:
                logger.info(f"  [DRY-RUN] Would write {img_file} and patch Qdrant for [{doc_name} p{page_num}]")
                total_patched += 1

        if next_offset is None:
            break
        offset = next_offset

    logger.info("=" * 60)
    logger.info(f"Backfill complete.")
    logger.info(f"  Scanned : {total_scanned}")
    logger.info(f"  Patched : {total_patched}")
    logger.info(f"  Skipped : {total_skipped}")
    if dry_run:
        logger.info("  (DRY-RUN — no changes were written)")
    logger.info("=" * 60)


def main():
    default_store = str(Path.home() / ".ask_me_store" / "vision_pages")
    parser = argparse.ArgumentParser(description="Backfill file_path in Qdrant payload from stored base64.")
    parser.add_argument("--host",       default=os.getenv("QDRANT_HOST", "127.0.0.1"))
    parser.add_argument("--port",       default=int(os.getenv("QDRANT_PORT", "6333")), type=int)
    parser.add_argument("--collection", default="vision_pages")
    parser.add_argument("--store-dir",  default=os.getenv("IMAGE_STORE_DIR", default_store))
    parser.add_argument("--dry-run",    action="store_true", help="Preview what would change without writing anything.")
    args = parser.parse_args()

    store_dir = Path(args.store_dir).expanduser().resolve()
    logger.info(f"Stable image store: {store_dir}")
    logger.info(f"Qdrant: {args.host}:{args.port}  collection: {args.collection}")
    if args.dry_run:
        logger.info("DRY-RUN mode — no files or Qdrant payloads will be modified.")

    backfill(
        host=args.host,
        port=args.port,
        collection=args.collection,
        store_dir=store_dir,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    main()
