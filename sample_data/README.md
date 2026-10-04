# Sample data

Synthetic, fictional industrial data only. No manufacturer manuals or proprietary plant data.

| Path | Contents |
| --- | --- |
| `equipment/registry.json` | Five assets including CNC-042 |
| `maintenance/records.json` | Inspection and PM history (offsets relative to seed time) |
| `maintenance/work_orders.json` | Historical and open work orders. CNC-042 has none open. |
| `telemetry/` | Generated at seed time, not checked in |

CNC-042 is the known overheating scenario: rising temperature, declining coolant flow, recurring `TEMP_HIGH` alarms, and an overdue cooling-system inspection.

Load into PostgreSQL:

```bash
python -m forgeflow.domain.seed --reset
```
