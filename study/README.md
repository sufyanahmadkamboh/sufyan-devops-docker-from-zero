# Study guide

Everything you need to study Docker from zero, also as one printable PDF: **[study-guide.pdf](study-guide.pdf)**
(the 23 lessons, the glossary, 25 interview questions and the knowledge checklist).

## How to study with this repository

| Step | Do this | Time |
|---|---|---|
| 1 | Read the lesson in [docs/](../docs/) to understand the idea | 15 min per lesson |
| 2 | Follow the matching chapter of the guided [tutorial/](../tutorial/README.md), typing every command | 30-60 min per chapter |
| 3 | Do the lab in [labs/](../labs/) on your own, including "Break it" | 30-45 min per lab |
| 4 | Solve the [challenges](../challenges/README.md) without opening the solutions | 15-30 min per topic |
| 5 | Practise the [troubleshooting](../troubleshooting/README.md) scenarios | 20 min each |
| 6 | Build and verify the [capstone](../capstone/README.md) | 60 min |
| 7 | Tick the [knowledge checklist](../CHECKLIST.md) and answer the [interview questions](interview-questions.md) | 30 min |

Total: about 15-20 hours for a careful first pass. The [roadmap](../ROADMAP.md) maps every stage to its tutorial
chapter, lab and lesson.

## Prerequisites

Basic terminal skills (`cd`, `ls`, `cat`, editing a text file), Docker installed ([docs/02](../docs/02-docker-installation.md)),
and Git. No programming knowledge is needed: the example applications are small and you never have to change their logic.

## Also in this folder

- [glossary.md](glossary.md): every Docker term used in the lab, in plain language
- [interview-questions.md](interview-questions.md): 25 questions with answers that point back to the labs
- [tools/build_pdf.py](tools/build_pdf.py): rebuilds the PDF from the Markdown lessons (`pip install markdown`)
