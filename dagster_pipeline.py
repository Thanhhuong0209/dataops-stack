"""
Dagster pipeline to read Parquet files and save data to VictoriaMetrics
"""
import os
import time
from pathlib import Path
from typing import Dict, List

import pandas as pd
import requests
from dagster import (
    AssetExecutionContext,
    Config,
    DefaultScheduleStatus,
    DefaultSensorStatus,
    Definitions,
    MaterializeResult,
    RunRequest,
    ScheduleDefinition,
    asset,
    define_asset_job,
    sensor,
)


class VictoriaMetricsConfig(Config):
    """Configuration for VictoriaMetrics connection."""

    vm_url: str = os.getenv("VICTORIAMETRICS_URL", "http://localhost:8428")
    batch_size: int = 1000


class VictoriaMetricsWriter:
    """Helper class to write data to VictoriaMetrics"""

    def __init__(self, vm_url: str, logger=None):
        self.vm_url = vm_url.rstrip('/')
        self.insert_url = f"{self.vm_url}/api/v1/import/prometheus"
        self.logger = logger  # Optional logger for better integration

    def _log(self, message: str, level: str = "info"):
        """Log message using logger if available, otherwise print"""
        if self.logger:
            if level == "error":
                self.logger.error(message)
            elif level == "warning":
                self.logger.warning(message)
            else:
                self.logger.info(message)
        else:
            print(message)

    def write_metrics(self, metrics: List[Dict], max_retries: int = 3) -> bool:
        """
        Write metrics to VictoriaMetrics using Prometheus format.

        Args:
            metrics: List of metric dicts with format:
                {
                    'name': 'metric_name',
                    'value': 123.45,
                    'timestamp': 1234567890,
                    'labels': {'label1': 'value1', 'label2': 'value2'}
                }

        Returns:
            True if successful, False otherwise.
        """
        for attempt in range(max_retries):
            try:
                lines = []
                for metric in metrics:
                    name = metric['name']
                    value = metric['value']
                    timestamp_ms = metric.get('timestamp', int(time.time() * 1000))

                    labels_str = ""
                    if metric.get('labels'):
                        label_pairs = [f'{k}="{v}"' for k, v in metric['labels'].items()]
                        labels_str = "{" + ",".join(label_pairs) + "}"

                    line = f"{name}{labels_str} {value} {timestamp_ms}"
                    lines.append(line)

                response = requests.post(
                    self.insert_url,
                    data='\n'.join(lines),
                    headers={'Content-Type': 'text/plain'},
                    timeout=30,
                )

                if response.status_code in [200, 204]:
                    return True

                error_msg = (
                    f"HTTP {response.status_code}: "
                    f"{response.text[:200] if response.text else 'No response body'}"
                )
                if attempt < max_retries - 1:
                    self._log(
                        f"VictoriaMetrics error (attempt {attempt + 1}/{max_retries}): "
                        f"{error_msg}, retrying...",
                        "warning",
                    )
                    time.sleep(1 * (attempt + 1))
                else:
                    self._log(f"VictoriaMetrics error (final attempt): {error_msg}", "error")
                    return False

            except requests.exceptions.ConnectionError as e:
                if attempt < max_retries - 1:
                    self._log(
                        f"VictoriaMetrics connection error "
                        f"(attempt {attempt + 1}/{max_retries}) to {self.insert_url}: "
                        f"{str(e)}, retrying...",
                        "warning",
                    )
                    time.sleep(1 * (attempt + 1))
                else:
                    self._log(
                        f"VictoriaMetrics connection error (final attempt) to "
                        f"{self.insert_url}: {str(e)}",
                        "error",
                    )
                    return False
            except requests.exceptions.Timeout as e:
                if attempt < max_retries - 1:
                    self._log(
                        f"VictoriaMetrics timeout (attempt {attempt + 1}/{max_retries}) "
                        f"to {self.insert_url}: {str(e)}, retrying...",
                        "warning",
                    )
                    time.sleep(1 * (attempt + 1))
                else:
                    self._log(
                        f"VictoriaMetrics timeout (final attempt) to {self.insert_url}: "
                        f"{str(e)}",
                        "error",
                    )
                    return False
            except Exception as e:
                if attempt < max_retries - 1:
                    self._log(
                        f"VictoriaMetrics unexpected error (attempt {attempt + 1}/"
                        f"{max_retries}): {str(e)}, retrying...",
                        "warning",
                    )
                    time.sleep(1 * (attempt + 1))
                else:
                    self._log(
                        f"VictoriaMetrics unexpected error (final attempt): {str(e)}",
                        "error",
                    )
                    return False

        return False


@asset(description="Read Parquet file and convert to DataFrame")
def read_parquet_data(context: AssetExecutionContext) -> pd.DataFrame:
    """
    Asset to read data from Parquet file.

    Expected Parquet schema:
    - timestamp: datetime or timestamp column
    - metric_name: string column with metric name
    - value: float column with metric value
    - Additional columns will be treated as labels
    """
    # Path to Parquet file (adjust as needed)
    parquet_path = Path("data/timeseries_data.parquet")

    if not parquet_path.exists():
        raise FileNotFoundError(f"Parquet file not found: {parquet_path}")

    context.log.info(f"Reading Parquet file: {parquet_path}")

    # Read Parquet file
    df = pd.read_parquet(parquet_path)

    context.log.info(f"Read {len(df)} rows from Parquet file")
    context.log.info(f"Columns: {df.columns.tolist()}")

    return df


@asset(
    description="Transform DataFrame to VictoriaMetrics format and write to VictoriaMetrics",
    deps=[read_parquet_data],
)
def write_to_victoriametrics(
    context: AssetExecutionContext,
    read_parquet_data: pd.DataFrame,
    config: VictoriaMetricsConfig,
) -> MaterializeResult:
    """
    Asset to transform DataFrame and write to VictoriaMetrics.

    Assumes the DataFrame has:
    - timestamp column (will be converted to milliseconds)
    - metric_name column (or uses default)
    - value column
    - Other columns as labels
    """
    # Override with environment variable if set
    vm_url = os.getenv("VICTORIAMETRICS_URL", config.vm_url)
    context.log.info(f"Using VictoriaMetrics URL: {vm_url}")
    # Get the DataFrame from previous asset
    df = read_parquet_data

    context.log.info(f"Processing {len(df)} rows for VictoriaMetrics")

    # Initialize writer with logger for better integration
    writer = VictoriaMetricsWriter(vm_url=vm_url, logger=context.log)

    # Convert DataFrame to metrics format
    metrics = []

    # Required columns
    required_cols = ['timestamp', 'value']

    # Check if required columns exist
    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"Required column '{col}' not found in DataFrame")

    # Determine metric name column
    metric_name_col = 'metric_name' if 'metric_name' in df.columns else None
    default_metric_name = 'parquet_metric'

    # Get label columns (all columns except timestamp, value, metric_name)
    label_cols = [col for col in df.columns
                  if col not in ['timestamp', 'value', 'metric_name']]

    # Convert timestamp to milliseconds if needed
    if pd.api.types.is_datetime64_any_dtype(df['timestamp']):
        df['timestamp_ms'] = df['timestamp'].astype('int64') // 10**6
    else:
        # Assume already in milliseconds or seconds
        df['timestamp_ms'] = df['timestamp'].astype('int64')
        # If values are too small, assume seconds and convert
        if df['timestamp_ms'].max() < 10**12:
            df['timestamp_ms'] = df['timestamp_ms'] * 1000

    # Convert DataFrame rows to metrics
    for _, row in df.iterrows():
        metric_name = row[metric_name_col] if metric_name_col else default_metric_name

        # Build labels
        labels = {}
        for col in label_cols:
            if pd.notna(row[col]):
                labels[col] = str(row[col])

        metric = {
            'name': str(metric_name),
            'value': float(row['value']),
            'timestamp': int(row['timestamp_ms']),
            'labels': labels
        }

        metrics.append(metric)

    context.log.info(f"Converted {len(metrics)} rows to metrics format")

    # Write to VictoriaMetrics in batches
    batch_size = config.batch_size
    total_batches = (len(metrics) + batch_size - 1) // batch_size
    successful_batches = 0
    failed_batches = 0

    context.log.info(
        f"Starting to write {len(metrics)} metrics in {total_batches} batches "
        f"(batch_size={batch_size})"
    )

    for i in range(0, len(metrics), batch_size):
        batch = metrics[i : i + batch_size]
        batch_num = i // batch_size + 1

        context.log.info(f"Writing batch {batch_num}/{total_batches} ({len(batch)} metrics)...")

        try:
            success = writer.write_metrics(batch)

            if success:
                successful_batches += 1
                context.log.info(f"[OK] Successfully wrote batch {batch_num}/{total_batches}")
            else:
                failed_batches += 1
                context.log.error(
                    f"[ERROR] Failed to write batch {batch_num}/{total_batches} "
                    f"to {vm_url} after retries"
                )
                context.log.error(f"VM URL: {vm_url}, Insert URL: {writer.insert_url}")
        except Exception as e:
            failed_batches += 1
            context.log.error(
                f"[EXCEPTION] Exception writing batch {batch_num}/{total_batches}: "
                f"{str(e)}"
            )
            context.log.error(f"VM URL: {vm_url}, Insert URL: {writer.insert_url}")
            import traceback

            context.log.error(traceback.format_exc())

    context.log.info(
        f"Write complete: {successful_batches} successful batches, "
        f"{failed_batches} failed batches"
    )

    if failed_batches > 0:
        raise Exception(f"Failed to write {failed_batches} batches to VictoriaMetrics")

    return MaterializeResult(
        metadata={
            "total_metrics": len(metrics),
            "successful_batches": successful_batches,
            "failed_batches": failed_batches,
            "vm_url": vm_url
        }
    )


# Define job for all assets
parquet_to_vm_job = define_asset_job(
    name="parquet_to_victoriametrics_job",
    selection=[read_parquet_data, write_to_victoriametrics],
)

# Define schedule to run daily
daily_schedule = ScheduleDefinition(
    name="daily_parquet_to_vm",
    cron_schedule="0 0 * * *",  # Run daily at midnight
    job=parquet_to_vm_job,
    default_status=DefaultScheduleStatus.RUNNING,
)


# Sensor to watch for new Parquet files
@sensor(
    name="parquet_file_sensor",
    minimum_interval_seconds=60,
    default_status=DefaultSensorStatus.STOPPED,
)
def parquet_file_sensor(context: AssetExecutionContext):
    """Sensor that triggers when new Parquet file is detected"""
    parquet_path = Path("data/timeseries_data.parquet")

    if parquet_path.exists():
        # Check file modification time
        mtime = parquet_path.stat().st_mtime

        # Get last run time from cursor
        last_run = float(context.cursor) if context.cursor else 0.0

        if mtime > last_run:
            context.log.info(f"New Parquet file detected: {parquet_path} (mtime: {mtime})")
            return RunRequest(
                run_key=f"parquet_to_vm_{int(mtime)}",
                job_name=parquet_to_vm_job.name,
                cursor=str(mtime)
            )

    return None


# Define all assets and resources
defs = Definitions(
    assets=[read_parquet_data, write_to_victoriametrics],
    schedules=[daily_schedule],
    sensors=[parquet_file_sensor],
)

