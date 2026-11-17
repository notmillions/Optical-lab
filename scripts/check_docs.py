from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FILES = [
    'README.md', 'AGENTS.md', 'docs/PRD.md', 'docs/ARCHITECTURE.md',
    'docs/SCIENTIFIC_METHOD.md', 'docs/ROADMAP.md', 'docs/SPRINTS.md',
    'docs/BACKLOG.md', 'docs/TEST_PLAN.md', 'docs/DATA_GOVERNANCE.md',
    'docs/adr/0001-evolutive-v1-tmm-v2-raytracing.md'
]
missing = [name for name in FILES if not (ROOT / name).is_file()]
if missing:
    raise SystemExit(f'Missing documentation: {missing}')
print('Documentation files present.')
