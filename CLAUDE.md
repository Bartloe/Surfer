# Surfer — projectspecifiek

> De algemene werkafspraken (taal, hoe ik praat, git-cadans, sessie-einde,
> codekwaliteit, script-standaard, enz.) staan één map hoger in `C:\VSCode\CLAUDE.md`
> en gelden ook hier. Hieronder alléén wat uniek is voor Surfer.

## Waar de projectkennis zit
- Projectstand: `~/.claude/projects/c--VSCode-Surfer/memory/` (index = `MEMORY.md`).
  Lees bij sessiestart eerst `stand-alone-app.md` (wegwijzer + actuele stand).
- **Actieve code: `C:\VSCode\Surfer\app`** (stand-alone app met GUI). Eigen `.venv` →
  draai met `app\.venv\Scripts\python.exe`. GUI starten: `app\start.bat`.
- `C:\VSCode\Surfer\poc` = gedeeld graafwerk (`surfer.scrapen`/`surfer.extractie`),
  wordt door `app` ongewijzigd hergebruikt; hier zelf niets aan wijzigen.

## Git
- Repo: `github.com/Bartloe/Surfer`. Push naar `main`.
