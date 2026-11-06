AUTONOMOUS MEMORY SYNC: I will never wait for the user to prompt me to save my memory. Whenever I complete a significant logical block, fix a bug, or change architecture, I will autonomously trigger my internal `/maestro-save` equivalent routine.

Specifically, I will independently update:
- `docs/CURRENT_STATE.md` — Modified Files, Blockers, Next Immediate Steps
- `docs/CHANGELOG.md` — dated entry with Added/Changed/Fixed/Files Modified sections
- `C:\Users\caeta\.claude\projects\C--Users-caeta-Desktop-app-escala\memory\` — any memory records affected by the session's decisions

This runs BEFORE concluding any response that modified code, DB schema, architecture decisions, or project docs. It is not optional and does not require a user prompt.

Trigger conditions (any one is sufficient):
- A new file was created or an existing file was meaningfully changed
- A DB schema decision was made
- A constraint or architectural rule was added or modified
- A phase task was completed or its status changed
- A new blocker was identified or an existing one was resolved
