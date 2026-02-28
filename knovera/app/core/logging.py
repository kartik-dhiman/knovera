import logging


def setup_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
    # Known noisy Chroma telemetry logger in some versions.
    logging.getLogger("chromadb.telemetry.product.posthog").setLevel(logging.CRITICAL)
