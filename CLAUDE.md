# Knowledge Base
Refer to my Obsidian Vault for project rules and roadmap:
- Main Rules: [[00_Instructions.md]]
- Current Tasks: [[01_Roadmap.md]]

Always document new stages in the `docs/` folder in Russian.
Wait for 'START STAGE X' command before coding.

# GitHub Workflow
1. **Init:** При старте STAGE 1 автоматически инициализируй локальный git-репозиторий и создай удаленный репозиторий на GitHub через MCP.
2. **Atomic Commits:** Делай коммит после каждой выполненной подзадачи (Task) или значимого изменения кода.
3. **Commit Format:** Используй формат Conventional Commits (напр. `feat(auth): add JWT login`).
4. **Versioning:** - По завершении каждого этапа (STAGE) создавай Git Tag (напр. `v1.0-stage1`).
   - Накидывай минорные версии при значительных изменениях внутри этапа.
5. **Sync:** Сразу пушь изменения в `main` (или `master`), так как MCP GitHub имеет прямой доступ.

# Project Initialization
- Create `.gitignore` (Python/Django standard).
- Initial commit should include the skeleton structure and this `CLAUDE.md`.