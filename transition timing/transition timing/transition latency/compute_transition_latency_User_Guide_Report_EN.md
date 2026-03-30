# compute_transition_latency.py User Guide Report

## 1. Document Information
- Document Title: compute_transition_latency.py User Guide Report
- Target Users: Data analysts, research staff, and project maintainers
- Applicable Script: compute_transition_latency.py
- Directory: transition latency

## 2. Script Overview
This script batch-computes transition latency between AOI (Area of Interest) segments, and exports event-level results, grouped statistics, and a visualization.

Core formula:

$$
\text{gap} = \text{start}_{B} - \text{end}_{A} = \text{start}_{B} - (\text{start}_{A} + \text{duration}_{A})
$$

Where:
- $A$ is the current AOI segment.
- $B$ is the next AOI segment in time.
- A larger $\text{gap}$ means a longer waiting time when switching from one AOI to the next.

## 3. Applicable Scenarios
- Compare AOI switching efficiency across stages (AOI2/AOI3/AOI4).
- Compare average transition latency across different blocking conditions.
- Support downstream visualization, statistical testing, and between-group analysis.

## 4. Input Data Specification
### 4.1 Source Directory
By default, the script scans input data from:

- Cours_03_ProjetRecherche_JinxuWEI/05.Recherche/AOI

To change the input directory, modify the variable `racine_week2` at the beginning of the script:

```python
racine_week2 = Path(r"/Cours_03_ProjetRecherche_JinxuWEI/05.Recherche/transition timing/transition latency")
```

Notes:
- It is recommended to use raw string syntax `r"..."` to avoid backslash escaping issues in Windows paths.
- If the path contains Chinese characters or spaces, keep it inside quotes.
- The current script uses a relative path, resolved from the working directory at runtime (usually the transition latency directory).
- Re-run the script after modification so it scans the new directory.

### 4.2 Stage Directories to Scan
Only the following three stage folders are processed:
- AOI2
- AOI3
- AOI4

Important: Even if the input directory contains other folders, the script only processes these three stage folders (controlled by `aoi_stages = ["AOI2", "AOI3", "AOI4"]`).

Simplified requirement: At the structural level, the input root only needs to contain AOI2, AOI3, and AOI4.

### 4.3 File Matching Rule
Inside each stage folder's subfolders (blocking), the script matches files named:

- *_ALL_AOI_combined_in_segments.csv

Example directory structure (minimum runnable setup):

```text
<input_root>
├─ AOI2
│  ├─ <blocking_1>
│  │  └─ xxx_ALL_AOI_combined_in_segments.csv
│  └─ <blocking_2>
│     └─ yyy_ALL_AOI_combined_in_segments.csv
├─ AOI3
│  └─ <blocking_1>
│     └─ zzz_ALL_AOI_combined_in_segments.csv
└─ AOI4
   └─ <blocking_1>
      └─ ppp_ALL_AOI_combined_in_segments.csv
```

If no CSV files match this pattern, the script will not fail, but no transition records will be produced for that directory.

### 4.4 Required Fields
Each input CSV must contain at least:
- AOI_Label
- Start_Time(s)
- Duration(s)

The script renames them internally to:
- aoi
- start
- dur

If required fields are missing, that file is skipped (excluded from aggregation).

### 4.5 Required Contents in the Input Directory
Before running, confirm the input directory meets these conditions:

1. Minimum requirement: The root contains AOI2, AOI3, and AOI4 folders.
2. To produce actual results: Place blocking subfolders under each stage, containing `*_ALL_AOI_combined_in_segments.csv` files.
3. Each CSV must include AOI_Label, Start_Time(s), and Duration(s), and time columns must be numeric.

Recommended pre-run checklist:
1. Verify the root directory is correct (`racine_week2` points to the target path).
2. Verify stage folder names are exactly AOI2/AOI3/AOI4.
3. Verify file names end with `_ALL_AOI_combined_in_segments.csv`.
4. Open a sample CSV and confirm the three required column names exactly match.

## 5. Processing Workflow
The script has two layers: per-file computation and global aggregation/export.

### 5.1 Per-file Computation
1. Read CSV.
2. Rename key columns (AOI_Label -> aoi, Start_Time(s) -> start, Duration(s) -> dur).
3. Sort by start in ascending order to ensure correct temporal sequence.
4. Compute end = start + dur.
5. Compress consecutive repeated AOIs:
   - If multiple consecutive rows have the same AOI, only keep the first row of that consecutive block.
6. Build adjacent transitions:
   - Current row is A, next row is B.
   - Compute aoi_suivant, start_suivant, and gap.
7. Remove the last row (no successor segment, so no transition).
8. Truncate negative gaps:
   - Set gap values < 0 to 0 (to handle slight overlap or rounding noise).

### 5.2 Global Aggregation
1. Merge transition events from all valid input files.
2. Add metadata fields:
   - stage
   - blocking
   - source_file
3. Export event table and grouped summary table.
4. Compute blocking-level statistics and generate a boxplot.

## 6. Output Description
Outputs are saved in the script directory.

### 6.1 transition_latency_events.csv (Event-level Details)
Fields:
- stage
- blocking
- source_file
- aoi
- aoi_suivant
- end
- start_suivant
- gap

Description: Each row is one concrete AOI transition event.

### 6.2 transition_latency_summary.csv (Transition-type Summary)
Grouping key: stage + blocking + aoi + aoi_suivant

Statistics:
- n (count)
- gap_moyen (mean latency)
- gap_median (median latency)
- gap_ecart_type (standard deviation)

Description: Used to compare latency differences among transition types across stages/conditions.

### 6.3 blocking_level_gap_stats.csv (Blocking-level Statistics)
Grouping key: stage + blocking

Statistics:
- mean_gap
- median_gap
- n_transitions

Stage-name mapping:
- AOI2 -> Apprentice work
- AOI3 -> Expert work
- AOI4 -> Apprentice assist

Description: Used for cross-blocking comparison of overall latency within each stage.

### 6.4 boxplot_mean_gap.svg (Visualization)
Figure content:
- Boxplot of mean_gap distribution by stage across blockings.
- Overlayed scatter points for each blocking-specific mean value.

Description: Used to identify between-stage distribution differences and potential outliers.

## 7. How to Run
Run one of the following commands in the script directory.

### 7.1 Using System Python
```powershell
python compute_transition_latency.py
```

### 7.2 Using Virtual Environment Python
```powershell
.\.venv\Scripts\python.exe compute_transition_latency.py
```

After execution, the terminal prints:
- Paths of generated CSV files
- Total number of computed transitions
- Paths of the stats file and figure

## 8. Result Interpretation Suggestions
- Start with transition_latency_summary.csv:
  - Filter low-frequency transitions by n first (to reduce small-sample instability).
  - Compare gap_moyen vs gap_median to check whether mean values are skewed by outliers.
- Combine blocking_level_gap_stats.csv with the boxplot:
  - Determine whether a stage has faster switching overall (lower mean_gap).
  - Identify outlier blockings and trace back to source_file.

## 9. Known Limitations and Risks
1. Consecutive repeated AOIs are reduced to the first row only; segment durations are not merged.
2. Negative gaps are clamped to zero, which may hide true overlap behavior.
3. The input root is hardcoded in the script, which reduces cross-machine portability.
4. No explicit handling for type anomalies, missing-value proportion, or outlier policy.
5. Uses matplotlib show(); adjustment may be needed in headless environments.

## 10. Maintenance and Extension Suggestions
1. Parameterize paths: add CLI arguments such as --input-root and --out-dir.
2. Improve logging: report skipped files and reasons (missing columns, empty files, parse failure).
3. Add data quality checks: field type and missing-value validation report.
4. Extend metrics: add quantiles, IQR, and file-level statistics.
5. Add automated tests: unit tests for gap logic, edge cases, and output schema.

## 11. Conclusion
The script reliably performs batch computation and baseline visualization of AOI transition latency, and is suitable as a foundational processing tool for stage-structure comparison in week5 analysis. By combining event-level detail with grouped summaries, it supports multi-level analysis from macro stage differences to micro transition patterns. With parameterization and quality-control enhancements, reusability and research traceability can be further improved.
