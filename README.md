# AIDS HTML transcripts

Claude Code and Codex conversation transcripts as one clickable page with three tabs
(Venheilheim, FocusBank, Lecture notes). Each turn shows the prompt, with the response
in a collapsed block below it.

Live: https://dasa108.github.io/aids-html-transcripts/

Each tab also has its own standalone page in `transcripts/` (`transcripts.html`,
`transcript_focusbank.html`, `transcript_lecture.html`).

## Interview prep

`prep/` holds published copies of the interview-prep pages (originally claude.ai artifacts),
linked from each tab (`PREP` in `build.py`):

- `prep/venheilheim-build.html`: The Venheilheim Build, interview course
- `prep/focusbank-learning-lab.html`: FocusBank Learning Lab, with an Interview Prep tab
- `prep/lecture-notes-field-guide.html`: Lecture Notes Field Guide, interview guide
- `prep/lecture-notes-course.html`: Lecture Notes Build Course

Saved answers and progress on these pages stay in each visitor's own browser.

## Adding or updating a transcript

1. Put the `.md` file in `transcripts/`. The raw `.md` files stay local and are not
   committed (see `.gitignore`); only the built HTML is published.
2. Add it to `TABS` in `build.py`, either as a new tab or as another part of an existing tab.
3. Run `python3 build.py`, then commit and push.

Claude Code `/export` files, `## User` / `## Claude` Markdown, Codex exports and Antigravity
exports all work.
Each tab uses its project website's colours and fonts (`STYLE` in `build.py`); the Venheilheim
fonts are in `fonts/` under the SIL Open Font License.
Anything listed in `REDACT` in `build.py` is replaced before publishing.
