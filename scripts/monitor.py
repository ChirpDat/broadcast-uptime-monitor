#!/usr/bin/env python3
import time
import yaml
import numpy as np
from rtlsdr import RtlSdr
from prometheus_client import Gauge, start_http_server

RF_POWER_DB = Gauge("broadcast_rf_power_db", "Estimated RF power in dB")
STATION_UP = Gauge("broadcast_station_up", "1 if station appears up, else 0")
STATE_CODE = Gauge("broadcast_station_state_code", "0=down, 1=up")
HEARTBEAT = Gauge("broadcast_monitor_heartbeat", "Unix timestamp of last successful loop")
MONITOR_FAULT = Gauge("broadcast_monitor_fault", "1 if monitor has a read or SDR fault, else 0")

def load_yaml(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def estimate_power_db(samples: np.ndarray) -> float:
    power = np.mean(np.abs(samples) ** 2)
    return float(10 * np.log10(power + 1e-12))

def open_sdr(freq: int, sample_rate: int, gain: float) -> RtlSdr:
    sdr = RtlSdr()
    sdr.sample_rate = sample_rate
    sdr.center_freq = freq
    sdr.gain = gain
    return sdr

def main() -> None:
    station_cfg = load_yaml("config/station.yaml")["station"]
    threshold_cfg = load_yaml("config/thresholds.yaml")["thresholds"]

    freq = station_cfg["frequency_hz"]
    sample_rate = station_cfg["sample_rate"]
    gain = station_cfg["gain"]
    samples_per_read = station_cfg["samples_per_read"]

    rf_power_min_db = threshold_cfg["rf_power_min_db"]
    poll_interval = threshold_cfg["poll_interval_seconds"]
    down_confirm_cycles = threshold_cfg["down_confirm_cycles"]
    up_confirm_cycles = threshold_cfg["up_confirm_cycles"]
    metrics_port = threshold_cfg.get("metrics_port", 9117)
    read_error_sleep = threshold_cfg.get("read_error_sleep_seconds", 3)

    start_http_server(metrics_port)

    bad_count = 0
    good_count = 0
    station_up = 1
    sdr = None

    print(f"Monitoring {station_cfg['name']} at {freq / 1e6:.1f} MHz")
    print(f"Threshold: {rf_power_min_db:.2f} dB")
    print(f"Prometheus metrics on :{metrics_port}/metrics")

    while True:
        try:
            if sdr is None:
                sdr = open_sdr(freq, sample_rate, gain)
                MONITOR_FAULT.set(0)

            samples = sdr.read_samples(samples_per_read)
            power_db = estimate_power_db(samples)

            RF_POWER_DB.set(power_db)
            HEARTBEAT.set(time.time())
            MONITOR_FAULT.set(0)

            if power_db < rf_power_min_db:
                bad_count += 1
                good_count = 0
            else:
                good_count += 1
                bad_count = 0

            if station_up == 1 and bad_count >= down_confirm_cycles:
                station_up = 0
                print(f"[ALERT] Station DOWN candidate confirmed. RF power: {power_db:.2f} dB")

            elif station_up == 0 and good_count >= up_confirm_cycles:
                station_up = 1
                print(f"[RECOVERY] Station UP confirmed. RF power: {power_db:.2f} dB")

            STATION_UP.set(station_up)
            STATE_CODE.set(station_up)

            print(
                f"power={power_db:.2f} dB | "
                f"station_up={station_up} | "
                f"bad_count={bad_count} | good_count={good_count}"
            )

            time.sleep(poll_interval)

        except Exception as e:
            print(f"[FAULT] SDR read failure: {e}")
            MONITOR_FAULT.set(1)
            HEARTBEAT.set(time.time())

            try:
                if sdr is not None:
                    sdr.close()
            except Exception:
                pass

            sdr = None
            time.sleep(read_error_sleep)

if __name__ == "__main__":
    main()
