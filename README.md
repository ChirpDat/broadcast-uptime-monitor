# Broadcast Uptime Monitor

An SDR-based off-air broadcast monitoring system built on Debian with Prometheus and Grafana.

## Current working features

- RF Power (dB) dashboard panel
- Monitor Fault dashboard panel
- Station Up dashboard panel
- Prometheus metrics export
- Grafana email alerting
- Station Down alert rule
- Monitor Fault alert rule

## Current live alert logic

### Station Down
- Query metric: `broadcast_station_up`
- Condition: `IS BELOW 0.5`
- Evaluation interval: every `10s`
- Pending period: `1m`

### Monitor Fault
- Query metric: `broadcast_monitor_fault`
- Condition: `IS ABOVE 0.5`
- Evaluation interval: every `10s`
- Pending period: `30s`

## Status

Working v1 prototype with dashboard and email alerting complete.
