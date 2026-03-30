# comparaison_structure_work.py User Guide

## 1. Purpose of This Document
This guide explains how to use comparaison_structure_work.py to perform a structural comparison between Apprentice work (AOI2) and Expert work (AOI3).

Based on existing transition result files, the script automatically generates:
- Transition probability matrices
- Heatmaps
- Entropy comparison
- Additional statistical summaries

## 2. Script Function Overview
This script performs the following 5 tasks:

1. Check whether required input files exist.
2. Build AOI2 and AOI3 category transition matrices (Glass/Paper/Tool) from event-level data.
3. Export matrix CSV files and corresponding SVG heatmaps.
4. Compute transition entropy (Shannon entropy) for each source category.
5. Generate Top-30 transition patterns and stage-level gap overview using summary and blocking stats.

## 3. Input File Requirements
By default, the script reads the following 3 files from its own directory:

- transition_latency_events.csv
- transition_latency_summary.csv
- blocking_level_gap_stats.csv

If any one of these files is missing, the script raises an error and stops.

### 3.1 transition_latency_events.csv (Required Fields)
Fields used by this script:
- aoi
- aoi_suivant
- stage

Purpose:
- Create from_cat / to_cat (Glass/Paper/Tool)
- Filter AOI2 and AOI3 event data
- Build transition probability matrices

### 3.2 transition_latency_summary.csv (Required Fields)
Fields used by this script:
- n
- gap_moyen

Purpose:
- Sort by n descending, then gap_moyen ascending
- Export top 30 rows to top30_transition_patterns.csv

### 3.3 blocking_level_gap_stats.csv (Required Fields)
Fields used by this script:
- stage
- mean_gap
- median_gap
- n_transitions
- blocking

Purpose:
- Generate stage-level summary table stage_gap_overview.csv

## 4. Categorization and Calculation Logic
### 4.1 AOI Text Mapping Rules
The mapper_aoi function applies these rules:

- Contains Glass -> Glass
- Contains Paper -> Paper
- Otherwise -> Tool

This means AOI labels that do not match Glass/Paper are grouped into Tool.

### 4.2 Transition Probability Matrix
The script performs cross-tab counting for from_cat -> to_cat, then row-normalizes to obtain a probability matrix.

Category order is fixed as:
- Glass
- Paper
- Tool

Even if a category is absent in current data, the row/column is kept and filled with 0 for easier cross-stage comparison.

### 4.3 Entropy Calculation
For each matrix row (one source category), the script computes Shannon entropy:

$$
H = -\sum_i p_i \log_2(p_i)
$$

Notes:
- Only probabilities greater than 0 are included.
- Higher entropy means more dispersed destination distribution.
- Lower entropy means more concentrated and predictable transitions.

## 5. Output Files
The script generates the following files in the same directory:

1. matrix_apprentice.csv
2. matrix_expert.csv
3. heatmap_apprentice.svg
4. heatmap_expert.svg
5. entropy_comparison.csv
6. top30_transition_patterns.csv
7. stage_gap_overview.csv

### 5.1 matrix_apprentice.csv / matrix_expert.csv
- Meaning: Category transition probability matrices for AOI2 / AOI3.
- Rows: Source category (from_cat).
- Columns: Target category (to_cat).
- Cell value: Probability of transitioning from a source category to a target category.

### 5.2 heatmap_apprentice.svg / heatmap_expert.svg
- Meaning: Heatmap visualization of the corresponding transition matrix.
- Darker color indicates higher probability.
- Used for intuitive comparison of transition structure differences between AOI2 and AOI3.

### 5.3 entropy_comparison.csv
- Row index: Glass / Paper / Tool.
- Columns:
  - entropy_apprentice
  - entropy_expert
- Used to compare transition complexity of the same source category between AOI2 and AOI3.

### 5.4 top30_transition_patterns.csv
- Source: Top 30 rows from transition_latency_summary.csv after sorting.
- Sort rule: n descending, gap_moyen ascending.
- Used for quickly identifying representative high-frequency and lower-latency transition patterns.

### 5.5 stage_gap_overview.csv
- Aggregated from blocking_level_gap_stats.csv by stage.
- Fields:
  - mean_of_mean_gap
  - median_of_median_gap
  - total_transitions
  - n_blockings
- Used for stage-level gap overview comparison.

## 6. How to Run
Run in the script directory:

```powershell
python comparaison_structure_work.py
```

Or use virtual environment Python:

```powershell
.\.venv\Scripts\python.exe comparaison_structure_work.py
```

After successful execution, the terminal prints:
- Output directory path
- Paths of the 3 input files actually used

## 7. Result Interpretation Suggestions
1. Start with matrix_apprentice.csv and matrix_expert.csv:
   - Compare row-wise distribution changes (same source category) across the two stages.
2. Then check entropy_comparison.csv:
   - Lower expert entropy suggests more stable/concentrated expert transitions.
   - Higher expert entropy suggests potentially more flexible/distributed expert strategy.
3. Combine with top30_transition_patterns.csv:
   - Check whether high-frequency patterns are also low-latency patterns.
4. Combine with stage_gap_overview.csv:
   - Evaluate whether overall latency performance is consistent at stage level.

## 8. Common Issues
### 8.1 Error: Missing input file
Cause: At least one of the 3 required input files is missing.
Fix: Ensure all required files are in the same directory as the script, with exact file names.

### 8.2 Output matrix is all zeros or almost all zeros
Possible causes:
- No AOI2 or AOI3 data in the stage column;
- Heavy missing values in aoi / aoi_suivant;
- Labels do not match Glass/Paper and are mostly grouped as Tool.
Fix: Check data coverage and label format in input files.

### 8.3 Heatmaps are generated but hard to compare
Suggested actions:
- Fix a shared color scale range (can be added in code later);
- Compare matrix CSV values together with heatmaps instead of relying on visual impression only.

## 9. Known Limitations
1. AOI categorization is simple and only based on substring matching.
2. No strict field-type validation (relies on pandas default parsing).
3. Only AOI2 and AOI3 are compared; AOI4 is not included in matrix/entropy analysis.
4. Heatmap style is basic; no unified color scale limits are set.

## 10. Maintenance Suggestions
1. Make input paths configurable (CLI arguments or config file).
2. Replace hardcoded if/else in mapper_aoi with a maintainable mapping table.
3. Add data-quality logs (missing ratios, category coverage, sample-size thresholds).
4. Add unit tests for edge cases such as empty data, missing columns, and single-category data.
