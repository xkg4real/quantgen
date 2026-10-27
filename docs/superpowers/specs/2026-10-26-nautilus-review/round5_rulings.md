# Round 5 (targeted): rulings, and the close of the Claude debate (Step 1a)

Date: 2026-10-26. Spec revision 5. Referees: ops and security (targeted, per `round4_rulings.md` §1). Both walked
Step 7A line by line, for a clean first attempt and for a second attempt after a failure at each line.

Tally: ops AGREE (5 minor), security AGREE (2 minor). No blocker, no major, nothing open from earlier rounds.

## 1. Closing ruling (C-8)

Round 5 raised only minor issues. Under C-8 the moderator applies them and **closes Step 1a** without a further round.
Final Claude verdicts by persona: security AGREE (rounds 2-5), quant AGREE (round 4), QA AGREE (rounds 3-4),
governance AGREE (rounds 3-4), ops AGREE (round 5).

Step 1b stays open: GPT (Codex CLI) and Gemini (Antigravity CLI) have not reviewed any revision, because neither CLI
exists in the cloud container. The review is REVIEW_INCOMPLETE for them until they run on the owner's machine (Codex
quota back 2026-10-30 14:40) or the owner records a substitute. Step 7A waits for Step 1b. Steps 2 to 7 start now on
the branch, on the section 2 defaults, with synthetic data and temp ledgers (GOVERNANCE-R2-1).

## 2. Rulings (all ACCEPT, applied in revision 6)

- OPS-R5-1 and SECURITY-R5-1 ACCEPT (one fix for both): the re-entry key is observable. While no
  `QUANTGEN-nautilus-block-out` rule exists, re-entry goes to the pip download line whatever `$q\wheels` holds (pip
  reuses every finished file whose hash it verifies). Once the rule exists, re-entry goes to the venv line; if
  `$q\wheels` is then missing, the owner first runs the elevated `Remove-NetFirewallRule` line and re-enters at the
  download line. The check is given as a command.
- OPS-R5-2 ACCEPT: "A throw in the five git lines stops the block: send Claude the message; the hand-off needs the
  branch." Line 1494 becomes `git merge --ff-only origin/claude/amazing-gauss-tdiguu` with its throw.
- OPS-R5-3 ACCEPT: 5.2.7 gives exit 0 for a replaced untracked baseline and for a tracked path with no file; L1-35
  adds both cases.
- OPS-R5-4 ACCEPT: R-14's Remedy adds the control-connect case; the runner prints the control error first.
- OPS-R5-5 ACCEPT: "add it if absent"; the nautilus suite's layer-2 tests hold `ES_CONTINUOUS | ES_SYSTEM_REQUIRED`
  on Windows; `$ProgressPreference = 'SilentlyContinue'` before `Invoke-WebRequest`.
- SECURITY-R5-2 ACCEPT: append `; if ($LASTEXITCODE) { throw "fixtures" }` to the `--record-baseline` line.

## 3. Rejected

None.
