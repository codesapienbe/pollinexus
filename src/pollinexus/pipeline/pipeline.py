"""Lightweight ML pipeline utilities for Pollinexus.

This module provides simple, production-ready placeholders for data
ingestion, training, evaluation, and model persistence. The functions
are designed to be importable and callable from the `trainer` service
in `docker-compose.yml`.
"""

from pathlib import Path
from typing import Any, Dict, Optional
import logging
import joblib
import json

import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report

from pollinexus.core.logging import get_logger, log_info, log_error

logger = get_logger(__name__)


def ingest(csv_path: str) -> pd.DataFrame:
    """Ingest CSV data from disk and perform light validation.

    Args:
        csv_path: Path to CSV file.

    Returns:
        DataFrame with ingested data.
    """
    try:
        log_info(f"Ingesting data from {csv_path}")
        df = pd.read_csv(csv_path)
        # Minimal validation: drop fully empty rows
        df = df.dropna(how="all")
        return df
    except Exception as exc:
        log_error(exc, {"csv_path": csv_path})
        raise


def train(
    data_path: Optional[str] = None,
    target_column: str = "target",
    model_output: str = "models/model.joblib",
    test_size: float = 0.2,
    random_state: int = 42,
    dry_run: bool = False
) -> Dict[str, Any]:
    """Train a simple RandomForest model on the provided dataset.

    If `dry_run` is True, performs preprocessing and validation without
    persisting the model.

    Returns a dictionary with training metrics and model path (if saved).
    """
    try:
        log_info("Starting training", {"data_path": data_path, "dry_run": dry_run})

        if data_path is None:
            raise ValueError("data_path is required for training")

        df = ingest(data_path)

        if target_column not in df.columns:
            raise ValueError(f"Target column '{target_column}' not present in data")

        X = df.drop(columns=[target_column])
        y = df[target_column]

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=random_state
        )

        model = RandomForestClassifier(random_state=random_state, n_estimators=100)
        model.fit(X_train, y_train)

        y_pred = model.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)
        report = classification_report(y_test, y_pred, output_dict=True)

        metrics = {
            "accuracy": accuracy,
            "report": report
        }

        if not dry_run:
            save_path = save_model(model, model_output)
            metrics["model_path"] = save_path

        log_info("Training completed", {"accuracy": accuracy})
        return metrics

    except Exception as exc:
        log_error(exc, {"data_path": data_path})
        raise


def evaluate(model_path: str, data_path: str, target_column: str = "target") -> Dict[str, Any]:
    """Evaluate a saved model against a dataset.

    Returns metrics dictionary.
    """
    try:
        log_info("Evaluating model", {"model_path": model_path, "data_path": data_path})
        model = joblib.load(model_path)
        df = ingest(data_path)

        if target_column not in df.columns:
            raise ValueError(f"Target column '{target_column}' not present in data")

        X = df.drop(columns=[target_column])
        y = df[target_column]

        y_pred = model.predict(X)
        accuracy = accuracy_score(y, y_pred)
        report = classification_report(y, y_pred, output_dict=True)

        metrics = {"accuracy": accuracy, "report": report}
        log_info("Evaluation completed", {"accuracy": accuracy})
        return metrics

    except Exception as exc:
        log_error(exc, {"model_path": model_path, "data_path": data_path})
        raise


def save_model(model: Any, output_path: str) -> str:
    """Persist model to disk with joblib and return the path."""
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, str(out))
    log_info(f"Model saved", {"path": str(out)})
    return str(out) 