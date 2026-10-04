# Telemetry

Hourly sensor history is generated at seed time, not stored as static files.

The CNC-042 scenario (last 30 days):

- rising spindle/coolant temperature
- declining coolant flow
- nine `TEMP_HIGH` alarms
- overdue cooling-system inspection

Re-generate with:

```bash
python -m forgeflow.domain.seed --reset
```
