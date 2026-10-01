"""
VictoriaMetrics ingestion test and smoke script.

Usage:
    python vm_ingestion_test.py --dry-run
    python vm_ingestion_test.py --vm-url http://localhost:8428
"""
import argparse
import json
import math
import os
import random
import time
from datetime import datetime, timedelta
from typing import Dict, List

import requests


class VictoriaMetricsWriter:
    """Helper class to write data to VictoriaMetrics."""

    def __init__(self, vm_url: str = "http://localhost:8428"):
        """
        Initialize VictoriaMetrics writer.

        Args:
            vm_url: VictoriaMetrics URL (default: http://localhost:8428)
        """
        self.vm_url = vm_url.rstrip('/')
        self.insert_url = f"{self.vm_url}/api/v1/import/prometheus"

    def write_metrics(self, metrics: List[Dict]) -> bool:
        """
        Write metrics to VictoriaMetrics using Prometheus format

        Returns:
            True if successful, False otherwise
        """
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
                print(f"Successfully wrote {len(metrics)} metrics to VictoriaMetrics")
                return True

            raise RuntimeError(f"HTTP {response.status_code}: {response.text[:200]}")

        except Exception as exc:
            print(f"Exception writing metrics to VictoriaMetrics: {exc}")
            raise


def generate_timeseries_data(
    start_time: datetime,
    end_time: datetime,
    interval_seconds: int = 60,
    metric_name: str = "sample_metric",
    labels: Dict[str, str] = None,
    value_pattern: str = "random",
    base_value: float = 50.0,
    amplitude: float = 20.0,
    sensor_index: int = 0,
    value_min: float = 0.0,
    value_max: float = 100.0,
) -> List[Dict]:
    """
    Generate synthetic time-series data for a metric.

    Supported value patterns:
    - random
    - sinusoid
    - sawtooth
    - spike
    """
    metrics = []
    current_time = start_time
    point_index = 0

    while current_time <= end_time:
        if value_pattern == "sinusoid":
            value = base_value + amplitude * math.sin((point_index + sensor_index) / 6)
        elif value_pattern == "sawtooth":
            cycle = (point_index + sensor_index) % 12
            value = base_value + amplitude * (cycle / 12)
        elif value_pattern == "spike":
            spike = 1 if (point_index + sensor_index) % 48 == 0 else 0
            value = base_value + amplitude * spike + random.uniform(-2.0, 2.0)
        else:
            value = random.uniform(value_min, value_max)

        if value_pattern != "random":
            value = max(value_min, min(value_max, value))

        timestamp_ms = int(current_time.timestamp() * 1000)

        metric = {
            'name': metric_name,
            'value': round(value, 3),
            'timestamp': timestamp_ms,
            'labels': labels or {}
        }

        metrics.append(metric)
        current_time += timedelta(seconds=interval_seconds)
        point_index += 1

    return metrics


def build_metric_profiles(
    profile: str,
    start_time: datetime,
    end_time: datetime,
    interval_seconds: int = 60,
    sensor_ids: List[str] = None,
    value_pattern: str = "random",
) -> List[Dict]:
    """Generate a realistic ingestion dataset based on a given profile."""
    sensor_ids = sensor_ids or [f"sensor_{index:02d}" for index in range(1, 4)]
    profile = profile.lower()

    profile_map = {
        "temperature": {
            "metric_name": "temperature_celsius",
            "labels_base": {"location": "room_a", "type": "temperature"},
            "base_value": 22.0,
            "amplitude": 8.0,
            "value_min": 10.0,
            "value_max": 38.0,
        },
        "humidity": {
            "metric_name": "humidity_percent",
            "labels_base": {"location": "room_a", "type": "humidity"},
            "base_value": 50.0,
            "amplitude": 18.0,
            "value_min": 20.0,
            "value_max": 90.0,
        },
        "cpu": {
            "metric_name": "cpu_usage_percent",
            "labels_base": {"location": "host_a", "type": "cpu"},
            "base_value": 55.0,
            "amplitude": 30.0,
            "value_min": 5.0,
            "value_max": 100.0,
        },
        "network": {
            "metric_name": "network_throughput_mbps",
            "labels_base": {"location": "edge_a", "type": "network"},
            "base_value": 120.0,
            "amplitude": 80.0,
            "value_min": 10.0,
            "value_max": 400.0,
        },
        "mixed": {
            "metric_name": "system_status",
            "labels_base": {"location": "room_a", "type": "mixed"},
            "base_value": 50.0,
            "amplitude": 25.0,
            "value_min": 0.0,
            "value_max": 100.0,
        },
    }

    if profile not in profile_map:
        raise ValueError(
            f"Unsupported profile '{profile}'. Supported profiles: {', '.join(sorted(profile_map))}"
        )

    config = profile_map[profile]
    all_metrics = []

    for sensor_index, sensor_id in enumerate(sensor_ids):
        labels = dict(config["labels_base"])
        labels["sensor_id"] = sensor_id
        metrics = generate_timeseries_data(
            start_time=start_time,
            end_time=end_time,
            interval_seconds=interval_seconds,
            metric_name=config["metric_name"],
            labels=labels,
            value_pattern=value_pattern,
            base_value=config["base_value"],
            amplitude=config["amplitude"],
            sensor_index=sensor_index,
            value_min=config["value_min"],
            value_max=config["value_max"],
        )
        all_metrics.extend(metrics)

    return all_metrics


def parse_args():
    parser = argparse.ArgumentParser(
        description="Generate and optionally write time series data to VictoriaMetrics."
    )
    parser.add_argument(
        "--vm-url",
        default=os.getenv("VICTORIAMETRICS_URL", "http://localhost:8428"),
        help="VictoriaMetrics endpoint",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Generate metrics without sending them to VictoriaMetrics",
    )
    parser.add_argument("--hours", type=int, default=24, help="Lookback window in hours")
    parser.add_argument(
        "--profile",
        default="temperature",
        choices=["temperature", "humidity", "cpu", "network", "mixed"],
        help="Metric profile to generate",
    )
    parser.add_argument(
        "--sensor-count",
        type=int,
        default=3,
        help="Number of sensor IDs to generate",
    )
    parser.add_argument(
        "--interval-seconds",
        type=int,
        default=60,
        help="Sampling interval in seconds",
    )
    parser.add_argument(
        "--value-pattern",
        default="random",
        choices=["random", "sinusoid", "sawtooth", "spike"],
        help="Value generation pattern for realistic ingestion tests",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=1000,
        help="Batch size for ingestion writes",
    )
    parser.add_argument(
        "--custom-labels",
        help="Optional JSON string for custom labels to attach to every sample",
    )
    return parser.parse_args()


def main():
    """Generate time series data and optionally publish it to VictoriaMetrics."""
    args = parse_args()
    print("Generating timeseries data...")

    vm_url = args.vm_url
    end_time = datetime.now()
    start_time = end_time - timedelta(hours=args.hours)

    sensor_ids = [f"sensor_{index:02d}" for index in range(1, args.sensor_count + 1)]
    custom_labels = {}
    if args.custom_labels:
        try:
            custom_labels = json.loads(args.custom_labels)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON for --custom-labels: {exc}") from exc

    all_metrics = build_metric_profiles(
        profile=args.profile,
        start_time=start_time,
        end_time=end_time,
        interval_seconds=args.interval_seconds,
        sensor_ids=sensor_ids,
        value_pattern=args.value_pattern,
    )

    if custom_labels:
        for metric in all_metrics:
            metric["labels"].update(custom_labels)

    print(f"Generated {len(all_metrics)} data points")
    print(f"Time range: {start_time} to {end_time}")
    print(f"Profile: {args.profile}")
    print(f"Value pattern: {args.value_pattern}")

    if args.dry_run:
        print("Dry run enabled: metrics were generated but not sent to VictoriaMetrics.")
        print(f"Target endpoint: {vm_url}")
        return

    writer = VictoriaMetricsWriter(vm_url=vm_url)
    total_batches = 0
    for i in range(0, len(all_metrics), args.batch_size):
        batch = all_metrics[i:i + args.batch_size]
        writer.write_metrics(batch)
        total_batches += 1
        time.sleep(0.1)

    print(f"Successfully generated and wrote {len(all_metrics)} metrics to VictoriaMetrics")
    print(f"Metrics profile: {args.profile}")
    print(f"Sensors: {', '.join(sensor_ids)}")
    print(f"Batches delivered: {total_batches}")


if __name__ == "__main__":
    main()

