# Tests: every lesson is executed

`tests/mdrun.py` reads a Markdown lesson and runs each `bash` code block in order, exactly as a learner would type it,
on a real Docker engine. A block passes when it exits with 0, unless it is marked as an expected failure. The GitHub
Actions workflow [test.yaml](../.github/workflows/test.yaml) runs every lesson on a fresh Linux machine on every change
and once a week, so the commands keep working when base images change.

You do not need any of this to learn Docker. It is here for maintainers, and as an example of testing documentation.

## Annotations

HTML comments directly above a block (invisible when GitHub renders the page):

| Annotation | Meaning |
|---|---|
| `<!-- test: skip -->` | not run: interactive (`-it`), follows logs forever, needs a browser or a Docker Hub login |
| `<!-- test: fail -->` | the block must fail (we break things on purpose) |
| `<!-- test: contains=TEXT -->` | the output must contain TEXT; several are separated with `;` |
| `<!-- test: absent=TEXT -->` | the output must not contain TEXT |
| `<!-- test: retry=N -->` | retry up to N times, 1 second apart (servers need a moment to start) |
| `<!-- test: timeout=S -->` | seconds before the block is stopped (default 300) |
| `<!-- test: output -->`, `output=head:N`, `output=tail:N` | with `--update`, the `text` block below is replaced by the real output |
| `<!-- test-run: COMMAND -->` | a hidden step: runs, but readers do not see it (waits, test-only cleanup) |

Every file starts in the repository root on a clean engine: **mdrun removes all containers, unused networks and
unused volumes before and after each file** (images are kept). That is why it refuses to run unless `CI` is set or you
confirm with `MDRUN_ALLOW_CLEANUP=1`. Do not run it on a machine whose containers you care about.

## Run it

```text
MDRUN_ALLOW_CLEANUP=1 python3 tests/mdrun.py labs/01-first-container/README.md
MDRUN_ALLOW_CLEANUP=1 python3 tests/mdrun.py --update labs/*/README.md      # also refresh the shown outputs
python3 tests/check_links.py                                                 # every relative link points somewhere
```
