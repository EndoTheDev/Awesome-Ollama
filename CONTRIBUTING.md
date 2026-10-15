# Contributing

Your contributions are always welcome!

## Entry format

Every entry is one row in a section table, four columns:

```
| [Name](link) | Description | Install | License |
```

Run `python scripts/lint.py README.md` before opening a PR — it must pass.
`python scripts/lint.py README.md --fix` fixes cell padding for you.

## Rules

- **One entry per Pull Request.**
- **Link**: open-source entries link to their **GitHub or GitLab repo**, not a
  landing page. Proprietary products link to their official site.
- **License**: the SPDX identifier (`MIT`, `Apache-2.0`, `GPL-3.0`, ...),
  `Custom` for non-SPDX licenses (modified MIT/Apache, fair-code), or
  `Proprietary`. Entries without a license are not open source.
- **Install**: values from this set only (comma-separated for several):
  `npm` · `pip` · `Docker` · `Download` · `Homebrew` · `Browser extension` ·
  `Marketplace` · `Maven` · `pub` · `NuGet` · `CocoaPods` · `Cargo` · `Source`
- **Description**: short and factual — say what the tool does. Don't mention
  Ollama (implied). No marketing: no `:heavy_check_mark:`, no `<br>`, no
  feature checklists. The License column already says if it's open source.
- **Table padding is enforced** by the linter; use `--fix`.
- **Search open Pull Requests first** — yours may be a duplicate.
- **Actively maintained**: entries are removed when the repo is dead (404),
  archived, unlicensed, or has had no push for over a year. Proprietary
  entries are judged by product activity instead.
- Adding a **new section**? Add the section table, its description, and its
  entry in the table of contents.

Everyone is welcome to submit.