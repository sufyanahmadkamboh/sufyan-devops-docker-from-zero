# LinkedIn package

| File | Use |
|---|---|
| `post.md` | Post text, written for a beginner audience |
| `carousel/carousel.pdf` | **Recommended:** upload as a *Document* post. LinkedIn shows it as a swipeable carousel |
| `carousel/slide-01.png` … `slide-11.png` | The same slides as images (1080×1350), for a multi-image post |
| `carousel/slides.html` | Source of the slides. Edit it and re-render each slide with a headless browser (`slides.html?s=N`) |
| `carousel/qr-repo.svg`, `qr-portfolio.svg` | The QR codes used on the last slide |
| `project-image.png` | Single architecture image (1200×627) |
| `project-summary.md` | Short technical summary |
| `hashtags.txt` | Hashtags |

## The slides (visual first: one picture per idea, short captions)

| # | Visual | Message |
|---|---|---|
| 1 | Staircase from `docker --version` to `docker compose up -d`: run, build, break, debug, fix | What it is, and the pain: tutorials stop at "hello world" |
| 2 | 4 panels: copy-paste, hidden failures, outdated steps, guessing | Why beginners get stuck |
| 3 | A road with 5 stops: theory, instructor, practice, emergencies, driving test | The idea: driving school, not a manual |
| 4 | Icon grid + "skip it when" panel | When to use it |
| 5 | 5-step timeline | How a learner uses it |
| 6 | Docker Engine with frontend and backend networks, web / api / db, volume | Capstone architecture |
| 7 | Learn → Build → Run → Break → Troubleshoot → Fix loop, and "every command tested" | How it works |
| 8 | Bar chart 1.75 GB → 212 MB → 108 MB, real error messages, verify.sh | Measured results (lab) |
| 9 | Number tiles: 23 / 18 / 12 / 10 / 19 / 1, video and PDF | Study material |
| 10 | Terminal staircase: clone, cd, cp secret, compose up, verify | Run it yourself |
| 11 | QR codes to the repository and portfolio, and a question | Links |

## How to post

1. Start a post, choose **Add a document**, and upload `carousel/carousel.pdf`.
2. Give it a title, for example *"Docker From Zero: learn Docker by breaking it"*.
3. Paste the text from `post.md`.
4. Optional: post `project-image.png` as a single image instead, or upload the 11 PNGs as a multi-image post.
5. Reply to comments about first Docker errors with the matching scenario in `troubleshooting/`.
