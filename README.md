# Agent Skills Repository

[![Repo Check](https://github.com/cuteweather/agent/actions/workflows/repo-check.yml/badge.svg)](https://github.com/cuteweather/agent/actions/workflows/repo-check.yml)

A collection of reusable agent skills for Codex/OpenCode, covering data preview, image workflows, and psychology stimulus reproduction pipelines.

## What This Repo Is

This repository contains 16 standalone skills. Each skill lives in its own directory and is designed to be installed into a Codex/OpenCode skills folder.

Typical use cases include:

- Previewing structured and unstructured files such as PDF, Office documents, archives, and MAT files
- Running image search and image generation workflows
- Executing function-shell style tasks with structured outputs
- Supporting end-to-end psychology stimulus reproduction workflows, including design extraction, grounding, code generation, review, and evaluation

## Quick Start

Clone the repository:

```powershell
git clone https://github.com/cuteweather/agent.git
cd agent
```

Install all skills into the default Codex skills directory:

```powershell
python .\scripts\install_skills.py
```

Install selected skills only:

```powershell
python .\scripts\install_skills.py image-search image-generate
```

Install to a custom target:

```powershell
python .\scripts\install_skills.py --target C:\path\to\skills --force
```

## How Skills Are Organized

Each skill directory contains at least one `SKILL.md`.

Optional subdirectories:

- `scripts/`: executable helpers or deterministic utilities
- `references/`: supporting docs loaded only when needed
- `assets/`: files used by the skill but not intended as inline documentation

Repository-level helper files:

- `skills.json`: generated machine-readable catalog
- `scripts/generate_skill_index.py`: rebuilds `skills.json`
- `scripts/install_skills.py`: installs skill folders into a target directory
- `scripts/check_repo.py`: validates repository consistency and scans for common secret patterns

## Skill Catalog

### Utility Skills

| Skill | Purpose |
| --- | --- |
| `data-preview` | Preview text and non-text data such as PDF, xlsx, docx, pptx, mat, zip, and rar files |
| `function-shell-executor` | Execute function-shell tasks and write structured results |
| `image-generate` | Generate images from prompts and save them locally |
| `image-search` | Search and download real image assets from Pexels |

### Stimuli Pipeline Skills

| Skill | Purpose |
| --- | --- |
| `stimuli-action-executor` | Execute a single workflow action with structured output |
| `stimuli-code-generation` | Generate scene composition, scheduling, and full experiment code |
| `stimuli-code-review` | Manual gate for `run_review` |
| `stimuli-dataset-evaluation` | Evaluate generated stimulus datasets and analyze tuning value |
| `stimuli-exp-design` | Extract executable experiment design specs from papers and data |
| `stimuli-exp-design-review` | Review and gate `exp_design.md` before downstream generation |
| `stimuli-grounding-segmentation` | Run grounding and segmentation on paper reference figures |
| `stimuli-meta-orchestrator` | Choose the next workflow action from manifest state |
| `stimuli-reproducibility-check` | Check whether a paper's stimuli are reproducible |
| `stimuli-result-report` | Refresh `result_report.md` from workspace and manifest state |
| `stimuli-unit-code-generation` | Generate primitive-level drawing functions and unit catalog |
| `stimuli-unit-function-review` | Manual gate for `run_unit_review` |

## Environment Variables

Some scripts require external API credentials. Set them before use:

- `PEXELS_API_KEY`
- `MINIMAX_API_KEY`
- Optional: `MINIMAX_API_URL`

## For Maintainers

Rebuild the skill index after adding, removing, or updating skill frontmatter:

```powershell
python .\scripts\generate_skill_index.py
```

Run repository checks before pushing changes:

```powershell
python .\scripts\check_repo.py
```

Current checks include:

- `SKILL.md` frontmatter completeness
- `skills.json` freshness
- common secret-pattern scanning

## GitHub Project Files

This repository includes:

- GitHub Actions validation workflow
- issue templates
- pull request template
- contributing guide
- security guide

## License

License has not been chosen yet. Add a `LICENSE` file before broader public reuse if you want to define explicit reuse terms.
