# Broadcast Uptime Monitor

An SDR-based off-air broadcast monitoring system built on Debian with Prometheus and Grafana.

This project monitors a radio station off-air, exports health and RF metrics to Prometheus, visualizes the station state in Grafana, and sends email alerts when the station appears down or when the monitor itself reports a fault.

## Why this project exists

A transmitter chain can look healthy internally while the station is actually off-air. This project adds an external verification layer by watching the signal off-air and turning that observation into operational telemetry.

In simple terms, it answers two questions:

- Is the station still on the air?
- Is the monitor itself healthy?

## Current working features

### Dashboard
The Grafana dashboard currently includes:

- **RF Power (dB)**
- **Monitor Fault**
- **Station Up**

### Metrics
The monitor exports these Prometheus metrics:

- `broadcast_station_up`
- `broadcast_monitor_fault`
- `broadcast_rf_power_db`
- `broadcast_monitor_heartbeat`
- `broadcast_station_state_code`

### Alerting
Grafana email alerting is configured and working for:

- **Station Down**
- **Monitor Fault**

Both firing and resolved notifications have been tested successfully.

## Current live alert logic

### Station Down
- **Query metric:** `broadcast_station_up`
- **Condition:** `IS BELOW 0.5`
- **Evaluation interval:** every `10s`
- **Pending period:** `1m`

**Meaning:**  
If the monitor stops detecting the station and that condition remains true for one minute, Grafana sends an email alert.

### Monitor Fault
- **Query metric:** `broadcast_monitor_fault`
- **Condition:** `IS ABOVE 0.5`
- **Evaluation interval:** every `10s`
- **Pending period:** `30s`

**Meaning:**  
If the monitor itself reports a fault for 30 seconds, Grafana sends an email alert.

## Plain-English explanation

### Station Down
This means the monitor cannot see the radio station anymore.

### Monitor Fault
This does **not** mean the station is down.  
It means the thing doing the watching may have a problem, so its readings should be checked carefully.

## Project structure

```text
broadcast-uptime-monitor/
├── README.md
├── LICENSE
├── config/
│   ├── station.yaml
│   └── thresholds.yaml
├── scripts/
│   └── monitor.py
└── systemd/
    └── broadcast-monitor.service
