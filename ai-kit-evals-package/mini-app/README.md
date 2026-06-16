# AI Kit Eval Dashboard Mini App

Mini Apps-compatible dashboard for AI Kit eval results.

## Run

```bash
pnpm install
pnpm dev
```

## Build

```bash
pnpm build
```

## Update Data

Generate fresh eval data from the package root:

```bash
python3 scripts/run_ai_kit_eval.py path/to/eval-runs.json --out-dir eval-output
cp eval-output/dashboard-data.json mini-app/src/data/dashboard-data.json
```

The app reads:

```text
src/data/dashboard-data.json
```

