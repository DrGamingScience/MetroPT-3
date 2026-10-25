# MetroPT-3 data card — PB03

Raw manifest: `D:\Downloads\MLDM\data\raw\sha256-978c4a95ef411383efe6bb86e35496d632fb23e6456b0a56973513e76c722c55\raw_manifest.json`
Dataset version: `sha256-978c4a95ef411383efe6bb86e35496d632fb23e6456b0a56973513e76c722c55`
CSV SHA-256: `db30ccb4ea402e3c8bf2c99db06e288d4f2a772f6928f9dbe26a920d69793e24`
Config hash: `5682fdfd2397ea08bf85dd24e85921b3693b9b33012c16ffe561002b991a881b`

## Cleaning and provenance

Raw rows: **1516948**; cleaned: **1516948**; valid: **1516948**; retained with sensor flags: **0**.
Time: 2020-02-01 00:00:00 → 2020-09-01 03:59:50 (original clock, no timezone).
Timestamp format: `%Y-%m-%d %H:%M:%S`. raw_row_id = zero-based CSV record position, scoped by dataset version; original index retained.
Exact duplicates compare parsed timestamp + all original sensor tokens, excluding the provenance index. Keep smallest raw_row_id; duplicate_count includes the representative. duplicate_rows.parquet maps every involved raw_row_id, including conflict groups.
Exact duplicate extra rows (including conflicts): 0; conflicting timestamps: 0 groups / 0 raw rows.
Disjoint removal reasons: `{"exact_duplicate_nonconflict": 0, "invalid_timestamp": 0, "timestamp_conflict": 0}`.
Raw row flags (may overlap): `{"infinity": 0, "invalid_digital": 0, "invalid_numeric": 0, "invalid_timestamp": 0, "missing_cell": 0}`.
Unparseable timestamps are excluded from cleaned and retained verbatim in issues.parquet. Every conflicting raw row is retained in conflicts.parquet. Sensor defects remain in cleaned with valid=false; no fill, resampling or silent row removal.
Missing cells mean blank/whitespace sensor tokens. Nonempty unparseable tokens (including NA/NaN/null) are invalid_numeric. Infinity is separate. Digital domain is {0, 1}; finite analog extremes and negative pressures are preserved.
2020-09-01 retained rows: **530**. No z-score/IQR filtering.

## Cadence and absent timestamps

delta0 = **10.0 s**; gap_break = **30.0 s**; a gap requires delta **>** gap_break. Segment IDs start at 0.
Fit scope: sorted unique non-conflicting timestamps strictly before train_end_exclusive; sensor defects do not remove timestamps. Boundary: 2020-03-01 00:00:00.
Minimum: one positive train delta; tied modes choose the smallest positive mode. Candidates: [10.0].
Train deltas: 214849 deltas; min/median/max: 9.0 / 10.0 / 28714.0 s; quantiles: {"0.01": 9.0, "0.05": 9.0, "0.25": 10.0, "0.75": 10.0, "0.95": 10.0, "0.99": 10.0}; five most frequent (seconds: count): 10.0s: 196033, 9.0s: 18780, 11.0s: 1, 252.0s: 1, 271.0s: 1. Full distribution is in Parquet metadata.
All-file deltas (quality audit only): 1516947 deltas; min/median/max: 8.0 / 10.0 / 172918.0 s; quantiles: {"0.01": 9.0, "0.05": 9.0, "0.25": 10.0, "0.75": 10.0, "0.95": 10.0, "0.99": 12.0}; five most frequent (seconds: count): 10.0s: 1337521, 9.0s: 128277, 12.0s: 38321, 13.0s: 7988, 11.0s: 4471. Full distribution is in Parquet metadata.
Gaps: **331**; segments: **332**; estimated absent cadence ticks: **378084**.
Total gap duration: 3274263.0 s; longest gap: 172918.0 s.
Absent ticks are sum(max(ceil(delta/delta0)-1, 0)), an estimate on the cleaned timeline, distinct from missing cells. No regular timestamp grid is asserted. gaps.parquet records only segment breaks, when present. Splits do not reset segment_id; downstream windows must enforce both split and segment boundaries.

## Calendar split summary (before PB05 window masks/purge)

| Split | Rows | Valid rows | First | Last |
| --- | ---: | ---: | --- | --- |
| train | 214850 | 214850 | 2020-02-01 00:00:00 | 2020-02-28 23:57:08 |
| validation | 429182 | 429182 | 2020-03-01 04:00:09 | 2020-04-30 23:39:23 |
| test | 872916 | 872916 | 2020-05-01 12:33:38 | 2020-09-01 03:59:50 |

## Sensor quality

All-file columns below are quality diagnostics only. Min/median/max describe finite raw train cells (before deduplication/conflict removal), not fitted preprocessing. Model/feature decisions must use train only.

| Sensor | Missing | Invalid numeric | Infinity | Outside digital domain | Unique numeric | Train finite min / median / max |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| TP2 | 0 | 0 | 0 | 0 | 5257 | -0.0300000000000011 / -0.0120000000000004 / 10.544 |
| TP3 | 0 | 0 | 0 | 0 | 3683 | 7.324 / 8.936 / 10.164 |
| H1 | 0 | 0 | 0 | 0 | 2665 | -0.0300000000000011 / 8.856 / 10.158 |
| DV_pressure | 0 | 0 | 0 | 0 | 2257 | -0.0279999999999986 / -0.0180000000000006 / 6.529999999999999 |
| Reservoirs | 0 | 0 | 0 | 0 | 3682 | 7.326 / 8.938 / 10.168 |
| Oil_temperature | 0 | 0 | 0 | 0 | 2462 | 31.974999999999994 / 56.62499999999999 / 69.15 |
| Motor_current | 0 | 0 | 0 | 0 | 1809 | 0.0199999999999995 / 0.0375000000000005 / 8.2925 |
| COMP | 0 | 0 | 0 | 0 | 2 | 0.0 / 1.0 / 1.0 |
| DV_eletric | 0 | 0 | 0 | 0 | 2 | 0.0 / 0.0 / 1.0 |
| Towers | 0 | 0 | 0 | 0 | 2 | 0.0 / 1.0 / 1.0 |
| MPG | 0 | 0 | 0 | 0 | 2 | 0.0 / 1.0 / 1.0 |
| LPS | 0 | 0 | 0 | 0 | 2 | 0.0 / 0.0 / 1.0 |
| Pressure_switch | 0 | 0 | 0 | 0 | 2 | 0.0 / 1.0 / 1.0 |
| Oil_level | 0 | 0 | 0 | 0 | 2 | 1.0 / 1.0 / 1.0 |
| Caudal_impulses | 0 | 0 | 0 | 0 | 2 | 1.0 / 1.0 / 1.0 |

## Cleaned schema

```json
{
  "": "string",
  "timestamp": "datetime64[us]",
  "raw_row_id": "int64",
  "TP2": "float64",
  "TP3": "float64",
  "H1": "float64",
  "DV_pressure": "float64",
  "Reservoirs": "float64",
  "Oil_temperature": "float64",
  "Motor_current": "float64",
  "COMP": "float64",
  "DV_eletric": "float64",
  "Towers": "float64",
  "MPG": "float64",
  "LPS": "float64",
  "Pressure_switch": "float64",
  "Oil_level": "float64",
  "Caudal_impulses": "float64",
  "invalid_timestamp": "bool",
  "missing_cell": "bool[pyarrow]",
  "invalid_numeric": "bool[pyarrow]",
  "infinity": "bool",
  "invalid_digital": "bool",
  "valid": "bool[pyarrow]",
  "duplicate_count": "int64",
  "segment_id": "int64",
  "split": "str"
}
```

Config snapshot, raw provenance and these statistics are stored in cleaned.parquet attrs['audit']. Optional detail tables are written only when nonempty.
