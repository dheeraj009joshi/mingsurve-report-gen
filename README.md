# MindSurve report generator

Builds PowerPoint reports from a study analysis export.

The default report is the Design Element Appeal deck in `Dafault-export/reportgen`. A second builder turns saved combination groups into a Design Combination Readout.

## Setup

Python 3.9 or newer.

```bash
cd Dafault-export
python3 -m pip install -r requirements.txt
```

Commands below are run from `Dafault-export`, so `reportgen` is on the import path.

## Default appeal report

`generate_report.py` reads `analysis_data.json` and writes a `.pptx`. The study type comes from the analysis (`Information Block` → `Study Type`). Pass `--study-type` when you need to override it.

| Type | What the deck draws |
|---|---|
| `layer` | One element from each layer, stacked into a pack |
| `grid` | Each winning image on its own, side by side |
| `text` | Full statements, with no image frame |
| `hybrid` | Uses the layer layout until hybrid data is available |

```bash
python3 generate_report.py redox/analysis_data.json -o redox/report.pptx
python3 generate_report.py Grid_study/analysis_data.json --study-type grid
python3 generate_report.py text_study/analysis_data.json --study-type text
python3 generate_report.py analysis_data.json --skip-images --logo brand_logo.png
```

`--skip-images` builds the deck without downloading artwork. If `study_data.json` sits next to the analysis file, its design constraints are applied.

### Call it from FastAPI

`create_default_report` does not import FastAPI. It accepts the analysis as a dict, JSON text, bytes, or a file path, and returns the PowerPoint bytes.

```python
from reportgen.default_report import DefaultReportError, create_default_report

report = create_default_report(analysis, study=study, study_type="grid")
# report.content, report.filename, report.media_type
```

To mount the routes:

```python
from reportgen.default_report_api import router

app.include_router(router, prefix="/api/v1")
```

That adds:

- `POST /api/v1/reports/appeal` — JSON body with `analysis`, optional `study`, `study_type`, and `download_images`
- `POST /api/v1/reports/appeal/upload` — multipart upload of the analysis file, plus optional study and logo files

A bad export raises `DefaultReportError`. The routes turn that into HTTP 400. The upload route needs FastAPI installed in the API project.

## Combination readout

`generate_combinations.py` builds the Design Combination Readout from saved groups and the study file.

```bash
python3 generate_combinations.py \
  "../special_question_report/saved_combinations.json" \
  "../special_question_report/study_data.json" \
  -o "../special_question_report/readout.pptx"
```

Each saved group is a segment. Inside a group, designs are split by metric: Top Down, Bottom Up, and Response Time. Pass `--analysis` when the analysis file is not discovered from the study id.

## Layout

```
Dafault-export/
  generate_report.py            default appeal deck
  generate_combinations.py      combination readout
  reportgen/                    builders, charts, and the FastAPI service
  redox/                        layer study sample
  Grid_study/                   grid study sample
  text_study/                   text study sample
special_question_report/        saved combinations and the readout sample
```
