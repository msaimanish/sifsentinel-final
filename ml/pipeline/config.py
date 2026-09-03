from pathlib import Path


# Project root:
# sifsentinel-final/
PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATA_DIR = PROJECT_ROOT / "data"

INCOMING_DIR = DATA_DIR / "incoming"
PROCESSED_DIR = DATA_DIR / "processed"

MODELS_DIR = PROJECT_ROOT / "ml" / "models"


def dataset_output_dir(dataset_id: str) -> Path:
    """
    Return the processing directory for a dataset.
    """
    return PROCESSED_DIR / dataset_id