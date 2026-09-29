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

`generate_combinations.py` builds the Design Combination Readout from saved combination groups. This is the special-questions deck: each saved group is one segment, and the designs inside it are split by metric (Top Down, Bottom Up, and Response Time).

The deck opens with a cover and a short “how to read lifts” slide. Each metric that appears in the file gets its own section. Inside a section, every saved group has a comparison chart and one detail slide per design.

It needs two files, and can use a third:

| File | Required | What it supplies |
|---|---|---|
| `saved_combinations.json` | yes | The saved groups, the selected elements, and each element’s lift |
| `study_data.json` | yes | Title, country, aspect ratio, and the study type when the items do not carry one |
| `analysis_data.json` | no | Base appeal, sample size, and launch date. Matched by study id when you pass `--analysis`, or when `analysis_data.json` sits beside the study file |

The same four study types as the appeal report apply here. The builder reads the type in this order: `--study-type` if you pass it, then `study_type` on each saved item, then `study_type` on the study file, then `Study Type` in the analysis.

| Type | What a saved combination draws |
|---|---|
| `layer` | One option from each layer, stacked into a single pack |
| `grid` | One image from each set, placed side by side. Images are not stacked |
| `text` | The full statement from each group. Sentences are not treated as image URLs |
| `hybrid` | Uses the layer layout until hybrid data is available |

```bash
python3 generate_combinations.py \
  "../special_question_report/saved_combinations.json" \
  "../special_question_report/study_data.json" \
  --analysis "../special_question_report/analysis_data.json" \
  -o "../special_question_report/readout.pptx"

python3 generate_combinations.py saved_combinations.json study_data.json --study-type grid
python3 generate_combinations.py saved_combinations.json study_data.json --study-type text --skip-images
```

`--skip-images` builds the deck without downloading artwork. Text studies skip image downloads on their own, because the element content is the statement.

### Call it from FastAPI

`build_combination_readout` does not import FastAPI. It takes file paths and writes the `.pptx` to `output_path`. It is not mounted on the appeal router. From a route, write the JSON you already hold into a temporary folder, call the builder, and stream the file back.

Add `Dafault-export` to the API process path, the same way as the appeal report.

```python
import io
import json
import tempfile
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from reportgen.combinations import build_combination_readout

router = APIRouter(prefix="/reports", tags=["reports"])
MEDIA = "application/vnd.openxmlformats-officedocument.presentationml.presentation"


@router.post("/combinations")
def create_combination_report(body: dict):
    try:
        with tempfile.TemporaryDirectory(prefix="combination-report-") as tmp:
            folder = Path(tmp)
            combinations_path = folder / "saved_combinations.json"
            study_path = folder / "study_data.json"
            output_path = folder / "readout.pptx"
            combinations_path.write_text(json.dumps(body["combinations"]), encoding="utf-8")
            study_path.write_text(json.dumps(body["study"]), encoding="utf-8")
            analysis_path = None
            if body.get("analysis") is not None:
                analysis_path = folder / "analysis_data.json"
                analysis_path.write_text(json.dumps(body["analysis"]), encoding="utf-8")
            built = build_combination_readout(
                combinations_path,
                study_path,
                output_path,
                analysis_path=analysis_path,
                download_images=body.get("download_images", True),
                study_type=body.get("study_type"),
            )
            content = built.read_bytes()
    except (ValueError, OSError, json.JSONDecodeError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return StreamingResponse(
        io.BytesIO(content),
        media_type=MEDIA,
        headers={"Content-Disposition": 'attachment; filename="Design Combination Readout v2.pptx"'},
    )
```

Mount it with the appeal router:

```python
app.include_router(router, prefix="/api/v1")
```

`POST /api/v1/reports/combinations` then takes `combinations`, `study`, and optional `analysis`, `study_type`, and `download_images`. Pass `analysis` when you have it. Without it, the deck still builds, but base appeal, sample size, and the launch date stay empty unless `analysis_data.json` is found beside the study file. Leave `study_type` out when the saved items or the study file already say `layer`, `grid`, `text`, or `hybrid`.

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
