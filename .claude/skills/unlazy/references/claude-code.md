# Unlazy on Claude Code

Unlazy is discipline plus a checker. Claude Code supplies four places to attach it. Only one of them enforces anything without model judgment; knowing which is the difference between a habit and a guarantee.

| Mechanism | Who decides | Enforcement |
|---|---|---|
| Skill invocation | the model, from the frontmatter description | none — a suggestion |
| Subagent dispatch | the driver | none — the leaf self-certifies |
| Parent `--reverify` | the driver, by running commands | real, but only if the driver runs it |
| Stop hook | the harness | structural — the only hard stop |

## Skill invocation

At session start Claude Code reads each skill's `name` and `description` into context. The body of `SKILL.md` loads only when the skill is invoked.

Two invocation paths:

- **Explicit:** `/unlazy` loads the skill deterministically. Use it when you know the task needs the ledger.
- **Automatic:** the model may invoke the skill when the task matches the description. This is a judgment call, not a rule. It can miss.

Consequences worth internalizing:

- The description is the entire trigger surface. Write it in the vocabulary the user actually uses, in every language they prompt in. A description naming another agent product, or a trigger syntax from another CLI, weakens the match for no benefit.
- Never promise a user that the skill "runs automatically". It becomes *available* automatically; invocation stays probabilistic. Only the Stop hook is deterministic.
- Do not create gates for a trivial edit just because the skill loaded. Loading is not a mandate.

## Subagent dispatch

A Depth Tree leaf maps to one Task/Agent tool call. The mapping is direct: leaf = subagent, `OWNS:` = the files it may write, leaf ledger = its acceptance contract.

Dispatch rules that matter on this platform:

- **Send independent leaves in one message.** Multiple tool calls in a single assistant message run concurrently; separate messages serialize. A tree whose leaves are dispatched one message at a time gets the coordination cost of parallelism with none of the wall-clock benefit.
- **Give a leaf only its brief.** The shared contract, its exact ownership, its dependencies, its ledger path, and the four-pass rule. Not the driver's transcript, not sibling leaf histories. A subagent starts with a fresh context; that isolation is the reason to use one, so do not spend it re-narrating.
- **A subagent's final report is its return value, not a conversation.** Ask for the ledger path and the measured counts, then verify them yourself.
- **Claim before dispatch.** Two concurrent leaves writing the same path will corrupt each other's work; the harness does not prevent this. Run `--claim` and honor a refusal.
- **Custom subagent types** defined in `.claude/agents/*.md` can carry a narrower tool set for mechanical leaves. Match the agent type to the leaf's actual needs rather than defaulting everything to a general-purpose agent.

## Parent verification

A returned subagent report is self-certification, and a self-certifying agent that ran out of context reports success as readily as one that succeeded. Re-run the leaf's runnable gates in the driver context:

```bash
node .claude/skills/unlazy/scripts/gate-check.mjs --root . --cwd . --reverify .unlazy/<scope>/gates/leaf-1.2.1.md
```

`--status` reads old evidence without executing anything; it is not verification. Use the same toolchain and declared shell the leaf used — a driver that verifies in a different environment is measuring something else.

## Stop hook

The hook is the only mechanism here that does not depend on the model choosing to cooperate. Claude Code runs it when a turn would end; while the resolved pipeline has unmet gates it returns `decision: "block"` and the turn continues instead of stopping.

Install writes a `hooks.Stop` entry:

```bash
node .claude/skills/unlazy/scripts/install-hooks.mjs            # .claude/settings.local.json (default)
node .claude/skills/unlazy/scripts/install-hooks.mjs --shared   # .claude/settings.json
node .claude/skills/unlazy/scripts/install-hooks.mjs --global   # ~/.claude/settings.json
node .claude/skills/unlazy/scripts/install-hooks.mjs --uninstall
```

Properties to know before installing:

- **Consent is required.** The hook changes how every session in that scope terminates. Offer it once; do not install it as a side effect of anything else.
- **It is scan-only.** The hook parses ledgers. It never executes a `CHECK:`, so it cannot be used to run commands, and it cannot tell whether a gate's English title matches what its command measures.
- **It releases after six blocks without ledger progress.** Progress is keyed to session and ledger content, so one session cannot consume another's budget. This exists so a bad ledger cannot trap a session forever — do not treat the sixth block as a normal working condition.
- **Default install is machine-local.** `--shared` writes this machine's absolute Node and script paths into project settings, which usually does not survive being cloned onto another machine and leaks local directory names.
- **A block costs a model turn.** The hook itself calls no model, but each block causes a continuation. Keep each block actionable — that is why the reason line names the outstanding gate ids.

Ignore the local coordination state:

```gitignore
.unlazy/
.unlazy-hook-state.json
.claude/settings.local.json
```

## A trap specific to nested skill directories

A skill installed at `.claude/skills/<name>/` carries its own subdirectories into your repository. A repository `.gitignore` rule written without a leading `/` applies at **every** depth, so a rule as ordinary as `scripts/` silently swallows `.claude/skills/unlazy/scripts/` — the entire checker — and `git status` reports nothing missing.

Before committing any skill, verify the file count actually staged:

```bash
git add .claude/skills/<name> && git status --porcelain --ignored .claude/skills/<name> | grep '^!!'
```

Anything listed is being dropped. Re-include it with a targeted negation rather than `git add -f`, so that later edits stay visible:

```gitignore
!.claude/skills/*/scripts/
```

This is not hypothetical: it is how this skill was first committed with 5 of its 26 files missing.

## Where each mode belongs

- **Solo ledger** — one focused session, one `GATES.md`. Most work lands here.
- **Orchestrated tree** — several coherent deliverables that benefit from fresh contexts. The driver plans, dispatches, re-verifies, and integrates.
- **Stop hook** — long autonomous runs where a premature stop is the failure mode you are actually trying to prevent.

Do not orchestrate what one context can implement and verify cleanly, and do not install a hook to solve a problem a single ledger already solves.
