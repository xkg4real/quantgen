export const meta = {
  name: 'quantgen-paper-write',
  description: 'QUANTGEN research paper, part 2: approval gate, implementation, study run, numbers and figures, English edition, referee panel, Korean edition, build and release state',
  whenToUse: 'Started by the quantgen-paper skill for /quantgen-paper write <paper_id> after the owner approved the scope, and for /quantgen-paper rereview <paper_id>.',
  phases: [
    { title: 'Gate', detail: 'tools.paper.approval check exit code; scope committed' },
    { title: 'Implement', detail: 'only the new code the approved protocol proposes' },
    { title: 'Study', detail: 'study/run.py, frozen inputs, MANIFEST, offline rerun' },
    { title: 'Figures', detail: 'per-language figures and tables, shared equations' },
    { title: 'Draft', detail: 'English edition and its claim rows' },
    { title: 'Review', detail: 'Claude, GPT via Codex and Gemini via agy; at most 2 rounds' },
    { title: 'Korean', detail: 'aligned translation, consistency check, fidelity and claim review' },
    { title: 'Build', detail: 'both PDFs, build records, meta.yaml, STATUS' },
  ],
}

const STATUSES = ['DRAFT', 'REVIEW_INCOMPLETE', 'BLOCKED_MAJOR', 'OWNER_REVIEW', 'RELEASED']
const a = args || {}
const ID = /^(fixture-)?(\d{4}-\d{2}-\d{2})-[a-z0-9]+(?:-[a-z0-9]+)*$/.exec(a.paper_id || '')
const MODE = a.mode || 'full'
if (!ID || !a.root || !a.now_utc || !['full', 'rereview'].includes(MODE)) {
  throw new Error('args must be {paper_id, root, now_utc, mode: "full" or "rereview", round?, only?, fidelity_only?, allow_private?}')
}
const ROOT = String(a.root).replace(/\\/g, '/').replace(/\/+$/, '')
const PID = a.paper_id
const REL = `papers/${PID}`
const P = `${ROOT}/${REL}`
const FIXTURE = Boolean(ID[1])
const PRIVATE = a.allow_private === true ? ' --allow-private' : ''
const AI_STATEMENT = 'This paper was prepared with AI assistance. Claude (Anthropic), through Claude Code, drafted the text and the study code under the author\'s direction and translated the English edition into Korean. GPT (OpenAI), through the Codex CLI, and Gemini (Google), through the Antigravity CLI, acted as simulated referees, and Gemini also reviewed the Korean translation for fidelity. The author chose the topic, approved the research protocol before the study was run, and has read and accepts every claim in this paper.'

const RULES = [
  `You are one stage of the QUANTGEN research-paper pipeline (spec: ${ROOT}/docs/superpowers/specs/2026-10-23-quantgen-split-and-paper-pipeline-design.md, section 5). The owner approved this paper's scope: ${P}/scope/ is frozen by scope/approval.json and must not change.`,
  `Repository root: ${ROOT}. Paper folder: ${P}. Paper id: ${PID}. Use absolute paths, run every python and git command with ${ROOT} as the working directory, and read and write text as UTF-8 with LF line endings.`,
  'Rules that bind this stage:',
  `- Write only inside ${P}, except where this stage names another path.`,
  '- Never edit anything under paper_live/ or grokteam/. core/engine/state.py, runtime.py, feed.py and __init__.py stay byte-identical; core/engine/orders.py, evaluator.py and ui/trading_page.py may only gain lines; GIT_HASH stays "UNVERSIONED" in core/ficc/macro_artifacts.py and core/quant/lab.py. No new pip packages; numpy 2.3.5, scipy 1.18.0 and pandas 2.3.3 do not change. Never run python -m paper_live.replay, grid, verdict, sameday or calibrate, or python -m grokteam.book. Never renormalise line endings (.gitattributes is "* -text").',
  '- Every number in the manuscript comes from study/numbers.json through \\qnum{key}. Never type a result by hand and never edit a result file.',
  '- Never invent a reference, page, equation number or quotation.',
  '- The owner\'s study materials (C:/Users/whydi/iCloudDrive/퀀트 학습 자료 and C:/Users/whydi/iCloudDrive/26년 2학기 수업자료) are private: never copy their text into en/, ko/, common/, study/, refs.yaml, refs.bib, claims.yaml or review/.',
  FIXTURE ? '- This is the synthetic fixture paper of the pipeline dry run: keep every artefact minimal.' : '',
  '- When this stage commits: stage only the paths it names (never git add -A or git add .), and end the message with a blank line and then the line Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>',
].filter(Boolean).join('\n')
const say = (...lines) => [RULES, ...lines].join('\n')

const LIST = { type: 'array', items: { type: 'string' } }
const STAGE = {
  type: 'object', required: ['ok', 'summary', 'problems'],
  properties: { ok: { type: 'boolean' }, summary: { type: 'string' }, problems: LIST },
}
const GATE = {
  type: 'object', required: ['approval_exit', 'approval_output', 'prereg_tracked', 'prereg_clean', 'status', 'reviewed'],
  properties: {
    approval_exit: { type: 'integer' }, approval_output: { type: 'string' },
    prereg_tracked: { type: 'boolean' }, prereg_clean: { type: 'boolean' }, status: { type: 'string' }, reviewed: LIST,
  },
}
const PANEL = {
  type: 'object', required: ['exit_code', 'statuses', 'reset_at'],
  properties: { exit_code: { type: 'integer' }, statuses: { type: 'object', additionalProperties: { type: 'string' } }, reset_at: LIST },
}
const STATUS = { type: 'object', required: ['status'], properties: { status: { type: 'string', enum: STATUSES } } }
const FINAL = { type: 'object', required: ['status', 'problems'], properties: { status: { type: 'string', enum: STATUSES }, problems: LIST } }

const blockers = []
const resets = []
const stop = (stage, r) => ({ status: 'STOPPED', paper_id: PID, stage, problems: r ? r.problems : [`the ${stage} agent returned nothing`], blockers })

// The gate reads the round just run (--round), never whatever round is highest on disk.
const statusOf = (k, label, ph) => agent(say(
  `Run python -m tools.paper.index gate ${REL} --round ${k} and return the one word it prints as status. Change nothing else.`,
), { label, phase: ph, schema: STATUS })

const claimsCheck = (label, ph) => agent(say(
  'Independent claim check. You did not write this manuscript; read it as a sceptical referee would.',
  `For every row of ${P}/claims.yaml whose status is not supported, or whose paragraph (its paragraph_id in ${P}/en/paper_en.tex) changed since the row was last checked (use git log and git diff), open the source at the locator and set status supported (support = the passage, at most 25 quoted words, or the derivation step), unsupported (with the reason) or unread (you could not open it). Never mark a row supported from memory.`,
  `Then run python -m tools.paper.claims ${REL}. ok=true only when it exits 0; otherwise problems = what it printed. Edit only ${REL}/claims.yaml, and commit it.`,
), { label, phase: ph, schema: STAGE })

const claudeReferee = (k, fidelity, label, ph) => agent(say(
  fidelity ? 'Korean fidelity review. You are a reviewer here, not the translator.' : `Referee, round ${k}. You are a referee here, not an author.`,
  `1. Run python -m tools.paper.panel ${REL} ${k} --bundle-only${fidelity ? ' --fidelity' : ''}${PRIVATE}. It prints the path of a fresh bundle.`,
  '2. Read REVIEW_BRIEF.md in that bundle and follow it. Read only files inside the bundle, never the repository or its review folder. From round 2 on the bundle\'s own review/ holds the previous round\'s reports and the authors\' response, which the brief tells you to read; no other referee\'s report of this round is there.',
  `3. Save your Markdown report to a scratch file outside the repository, then record it: python -m tools.paper.panel ${REL} ${k} --record claude <that file>${fidelity ? ' --fidelity' : ''}. It prints the record path and its status; a status other than ok means the report lacks one of the "## Major" and "## Minor" headings the brief requires, or its verdict is REJECT or NOT FAITHFUL while "## Major" is empty: fix its shape (every objection goes under "## Major" or "## Minor"), not its content, and record it again.`,
  'ok=true once the record is written with status ok; summary = your verdict line.',
), { label, phase: ph, schema: STAGE })

const cliPanel = (k, only, fidelity, label, ph) => agent(say(
  `Run the CLI referees: python -m tools.paper.panel ${REL} ${k}${only.length ? ' --only ' + only.join(',') : ''}${fidelity ? ' --fidelity' : ''}${PRIVATE}`,
  'Each referee may take up to 25 minutes, so start the command in the background and wait until it exits; never start it twice. It prints a JSON object of referee name to status and writes a record for every referee, whatever happened.',
  `Return its exit code, that JSON as statuses, and reset_at = the reset_at value of every record in ${P}/review/ whose status is "quota". Do not judge, retry or edit anything.`,
), { label, phase: ph, schema: PANEL })

// One review round: the Claude reviewer and the CLI reviewers side by side, then the gate.
// only: null = every reviewer; otherwise reviewer names, where "claude" is the Claude reviewer.
async function panelRound(k, only, fidelity, tag, ph) {
  const jobs = []
  let out = null
  if (!only || only.includes('claude')) jobs.push(() => claudeReferee(k, fidelity, `${tag}-claude`, ph))
  const cli = only ? only.filter(n => n !== 'claude') : []
  if (!only || cli.length) jobs.push(async () => { out = await cliPanel(k, cli, fidelity, `${tag}-cli`, ph); return out })
  await parallel(jobs)
  if (out) resets.push(...(out.reset_at || []))
  return statusOf(k, `${tag}-gate`, ph)
}

const revise = k => say(
  `Revision after referee round ${k}. You are the author.`,
  `1. Read every ${P}/review/round${k}_*.md. Write ${P}/review/response_round${k}.md: for each issue (its id and referee), what changed and where (section label and paragraph ids), or why no change was made. The round ${k + 1} referees read it, so it quotes nothing from the owner's private materials.`,
  `2. Revise ${P}/en/paper_en.tex. An analysis a referee requests goes only into a section "Exploratory analyses requested in review" (\\label{sec:exploratory}), produced by python ${REL}/study/run.py --kind exploratory --analysis <name> --now <current UTC time>, which writes a new run directory with its own MANIFEST and adds new numbers keys. Pre-specified results and their numbers never change.`,
  `3. Set status unread on the claims.yaml row of every paragraph you changed, add rows for new citations, run python -m tools.paper.refs verify ${REL} (it re-verifies every refs.yaml entry against Crossref or arXiv and rewrites refs.yaml and refs.bib; a stored record that no longer matches its entry blocks release), and recompile the English edition with tools.paper.build.compile_tex until it reports no errors.`,
  `4. Commit ${REL}/en, ${REL}/review/response_round${k}.md, ${REL}/claims.yaml, ${REL}/refs.yaml, ${REL}/refs.bib and any new ${REL}/study outputs.`,
)

// 0. The approval gate: an exit code, not a judgment
phase('Gate')
const gate = await agent(say(
  'Stage 0, the approval gate. Run exactly these commands from the repository root, report what they print, and change nothing:',
  `1. python -m tools.paper.approval check ${REL}   -> approval_exit = its exit code; approval_output = its last 40 lines.`,
  `2. git ls-files --error-unmatch ${REL}/scope/prereg.json   -> prereg_tracked = (exit code 0).`,
  `3. git status --porcelain -- ${REL}/scope   -> prereg_clean = (no output).`,
  `4. status = the single line of ${P}/STATUS, or "" when it is absent.`,
  `5. reviewed = the names of the files in ${P}/review/ that match round*_*.json or fidelity_*.json; [] when there are none or the folder is absent.`,
), { label: 'approval-gate', phase: 'Gate', schema: GATE })
if (!gate) return { status: 'REFUSED', paper_id: PID, reason: 'the approval gate returned nothing' }
if (gate.approval_exit !== 0 || !gate.prereg_tracked || !gate.prereg_clean) {
  return { status: 'REFUSED', paper_id: PID, reason: 'the scope is not approved as committed: tools.paper.approval check failed, or scope/ is not committed', detail: gate }
}
if (gate.status === 'RELEASED') return { status: 'REFUSED', paper_id: PID, reason: 'the paper is RELEASED; reopen it by hand first' }
// Review records from an earlier run would be read as this run's: a full run starts only on a paper without any.
if (!Array.isArray(gate.reviewed)) return { status: 'REFUSED', paper_id: PID, reason: 'the approval gate did not list the review records' }
if (MODE === 'full' && gate.reviewed.length) {
  return { status: 'REFUSED', paper_id: PID, reason: `${REL}/review already holds review records (${gate.reviewed.join(', ')}); a full run would mix them with its own. Use mode "rereview", or move ${REL}/review aside by hand first.` }
}
const ROUNDS = gate.reviewed.map(n => /^round(\d+)_/.exec(n)).filter(Boolean).map(m => Number(m[1]))
if (MODE === 'rereview' && ROUNDS.length && Number(a.round || 1) < Math.max(...ROUNDS)) {
  return { status: 'REFUSED', paper_id: PID, reason: `round ${Number(a.round || 1)} is older than the latest review round ${Math.max(...ROUNDS)}; rereview that round instead` }
}

if (MODE === 'full') {
  // 6. Implementation, only what the approved protocol proposes
  phase('Implement')
  const impl = await agent(say(
    'Stage 6, implementation: only what the approved protocol proposes.',
    `Read ${P}/scope/protocol.md (Proposed new code) and ${P}/scope/prereg.json (new_code). If they propose no reusable repository module, change nothing and return ok=true with summary "no new code".`,
    'Otherwise implement exactly the proposed reusable modules, test first. Each gets an acceptance module exposing tests() -> list[(name, fn)], registered in tests/run_all.py through a lazy import inside a function (an ImportError becomes one NOT_RUN entry). Paper-specific code does not belong here; it goes in study/ in the next stage. UI and Primer integration is out of scope.',
    'While you work, python tests/run_all.py --suite <each suite you touched> is fine, but each --suite run rewrites qa/acceptance_results.json with its own rows alone. Before you commit, run the full python tests/run_all.py (no --suite; about 11 minutes) and python -m tests.macro_m0_harness: neither may show a FAIL. If a defect turns up in a file pinned by a frozen study, fix it on the main line and say in the summary that the study of record runs from the tag studies-of-record-2026-10-23.',
    'Commit the new modules, their tests, tests/run_all.py and the qa/acceptance_results.json that the full run wrote, together; never commit that file from a --suite run.',
  ), { label: 'implement', phase: 'Implement', schema: STAGE })
  if (!impl || !impl.ok) return stop('implement', impl)

  // 7. The study run
  phase('Study')
  const study = await agent(say(
    'Stage 7, the study run.',
    `1. Check every pinned_code sha256 in ${P}/scope/prereg.json against the working tree (tools.paper.study.start_run refuses on a mismatch too). On any mismatch stop: ok=false, problems = the files (the owner must re-approve an amended protocol).`,
    `2. Write ${P}/study/run.py (helpers may go in other ${P}/study/*.py files) implementing exactly the analyses and variants of scope/protocol.md and nothing more. It begins with sys.path.insert(0, str(Path(__file__).resolve().parents[3])) so the repository imports resolve. It accepts --now (UTC, YYYY-MM-DDTHH:MM:SSZ), --offline, --kind (default: the prereg run_kind) and --analysis (default: every pre-specified analysis). It uses tools.paper.study: ctx = start_run(paper_dir, kind=..., seed=<prereg seed>, command=" ".join(sys.argv), now_utc=<--now>); every raw input passes through freeze_input(ctx, name, data) before use, and --offline reads the inputs back from study/data/ instead of fetching; trials, if the protocol registers any, go only to the ledger family PAPER-${PID} under paper_ledger_dir(paper_dir), never to ~/.nextgen/macro/ledgers; finish(ctx, results, qualification=...) where qualification is one of tools.paper.study.QUALIFICATIONS (read the tuple from tools/paper/study.py: "qualified", "insufficient_data", "smoke_only" or "not_run"), as it truly is. Except with --offline, it then merges its keys into study/numbers.json and study/numbers.tex with tools.paper.numbers (load_numbers, then write_numbers), each key with value, fmt, source ("runs/<run_id>/results.json:<field>"), selection and units; keys match ^[a-z0-9_]+$. With --offline it writes only its own new run directory study/runs/<run_id>/ (freeze_input finds study/data/ unchanged): it registers no ledger trial and never rewrites study/numbers.json or study/numbers.tex, which keep their sources in the online run.`,
    `3. Commit ${REL}/study/*.py before running: start_run refuses an uncommitted prereg and, for a pre-specified or confirmatory run, a dirty tree.`,
    `4. Run python ${REL}/study/run.py --now <the current UTC time from the system clock>. Commit ${REL}/study/data, ${REL}/study/runs, ${REL}/study/ledgers (if it exists), ${REL}/study/numbers.json and ${REL}/study/numbers.tex.`,
    `5. The offline rerun: python ${REL}/study/run.py --offline --now <a later UTC time>. tools.paper.study.compare_runs(<first run dir>, <second run dir>) must return []; otherwise stop with what it returned. Then git status --porcelain -- ${REL}/study/numbers.json ${REL}/study/numbers.tex must print nothing, and git status --porcelain -- ${REL}/study must list only the second run directory; otherwise stop: ok=false with that output (the rerun rewrote something besides its own run). Commit the second run directory.`,
    'Return ok=false with the reason if any step fails. Never edit a result or a number by hand.',
  ), { label: 'study', phase: 'Study', schema: STAGE })
  if (!study || !study.ok) return stop('study', study)

  // 8. Numbers, figures and tables
  phase('Figures')
  const figs = await agent(say(
    'Stage 8, numbers, figures and tables.',
    `1. Check that every key of ${P}/study/numbers.json has value, fmt, source, selection and units, and that ${P}/study/numbers.tex defines every key.`,
    `2. Write ${P}/study/figures.py and run it. Each figure is rendered from the latest study/runs/*/results.json twice, lang="en" into ${P}/en/figures/ and lang="ko" into ${P}/ko/figures/ (PDF), with Korean text set in the font file C:/Windows/Fonts/malgun.ttf (matplotlib.font_manager.FontProperties(fname=...)); or the figure carries no words and only its caption is translated.`,
    `3. Write ${P}/study/tables.py and run it. Each table is generated from numbers.json into ${P}/en/tables/<name>.tex and ${P}/ko/tables/<name>.tex: booktabs, per-language headers, every cell a \\qnum{key}, and no literal digit anywhere in the tabular (a digit a header needs goes in math mode, for example $h=1$). tools.paper.consistency inlines these files and checks them.`,
    `4. Put the shared equations in ${P}/common/<name>.tex (math only, no prose) for both editions to \\input.`,
    `5. Commit ${REL}/study/figures.py, ${REL}/study/tables.py, ${REL}/en/figures, ${REL}/ko/figures, ${REL}/en/tables, ${REL}/ko/tables and ${REL}/common.`,
  ), { label: 'figures', phase: 'Figures', schema: STAGE })
  if (!figs || !figs.ok) return stop('figures', figs)

  // 9. The English edition
  phase('Draft')
  const draft = await agent(say(
    'Stage 9, the English edition. You are the author.',
    `Write ${P}/en/paper_en.tex from ${ROOT}/tools/paper/template_en.tex; read the template and ${ROOT}/tools/paper/qgpaper.sty first.`,
    '- Front matter: the title; the author Geon Koh, Korea University; the abstract; keywords; JEL codes; \\paperstatus{...} carrying the scientific status from the claim labels and the run qualification.',
    '- Sections, each with \\label{sec:<id>}: introduction, literature, model, data, results (\\label{sec:results}), robustness (\\label{sec:robustness}), implementation (how QUANTGEN implements the method, its gaps and guardrails, from scope/integration.md, with module paths), conclusion.',
    '- Every paragraph is preceded by its own line "% id: <section>-<n>". The literature paragraphs keep the ids planned in scope/literature.md.',
    '- Every number in the abstract, results, robustness and tables is \\qnum{key}. Equations are \\input from ../common/, tables from tables/, figures from figures/.',
    '- A result whose run qualification is not_run, smoke_only or insufficient_data is never stated as a finding; its status appears in the abstract and the conclusion.',
    `- The aistatement environment holds this text, changed only where the tools actually used differ: "${AI_STATEMENT}"`,
    '- A closing note: "This paper is research. It is not investment advice."',
    `- Add a ${P}/claims.yaml row (status unread) for every \\cite in the model and results sections, keyed to its paragraph id. The literature rows exist already; update their paragraph_id only where a paragraph moved.`,
    `- Run python -m tools.paper.refs verify ${REL}: it re-verifies every refs.yaml entry against Crossref or arXiv and rewrites refs.yaml and refs.bib (an entry added or edited since the research stage needs it).`,
    `Compile the English edition alone with tools.paper.build.compile_tex(Path("${P}/en/paper_en.tex")) and fix every error it reports (warnings may stay; list them in the summary). Commit ${REL}/en/paper_en.tex, ${REL}/claims.yaml, ${REL}/refs.yaml and ${REL}/refs.bib.`,
  ), { label: 'draft-en', phase: 'Draft', schema: STAGE })
  if (!draft || !draft.ok) return stop('draft', draft)
  let checked = await claimsCheck('claims-en', 'Draft')
  if (!checked || !checked.ok) {
    const fix = await agent(say(
      'Claim repair. You are the author.',
      `Read the problems python -m tools.paper.claims ${REL} prints and the unsupported or unread rows of ${P}/claims.yaml. For each, find a source that supports the claim and fix the row, or weaken or remove the claim in ${P}/en/paper_en.tex. Never cite a source for something it does not say. Recompile with tools.paper.build.compile_tex and commit ${REL}/en/paper_en.tex and ${REL}/claims.yaml.`,
    ), { label: 'claims-fix', phase: 'Draft', schema: STAGE })
    if (!fix || !fix.ok) return stop('claims-fix', fix)
    checked = await claimsCheck('claims-en-2', 'Draft')
    if (!checked || !checked.ok) blockers.push(...(checked ? checked.problems : ['the second claim check returned nothing']))
  }
}

// 10. The referee panel: at most 2 rounds; the round limit never clears a veto
phase('Review')
let k = MODE === 'rereview' ? Number(a.round || 1) : 1
let revised = MODE === 'full'
let st = null
if (MODE === 'full' || (a.only || []).length) {
  st = await panelRound(k, MODE === 'full' ? null : a.only, false, `r${k}`, 'Review')
  if (!st) return stop('review', null)
  while (st.status === 'BLOCKED_MAJOR' && k < 2) {
    const rev = await agent(revise(k), { label: `revise-r${k}`, phase: 'Review', schema: STAGE })
    if (!rev || !rev.ok) return stop(`revise-r${k}`, rev)
    revised = true
    const rc = await claimsCheck(`claims-r${k}`, 'Review')
    if (!rc || !rc.ok) blockers.push(...(rc ? rc.problems : [`the claim check after round ${k} returned nothing`]))
    k += 1
    st = await panelRound(k, null, false, `r${k}`, 'Review')
    if (!st) return stop('review', null)
  }
  if (st.status === 'BLOCKED_MAJOR') {
    return {
      status: 'BLOCKED_MAJOR', paper_id: PID, round: k, reset_at: resets, blockers,
      next: `Major issues remain after round ${k}. The round limit stops the work; it does not clear the veto. Show the owner ${REL}/review/round${k}_*.md.`,
    }
  }
}

// 11. The Korean edition and its fidelity review (which also rechecks every claims.yaml row against the Korean)
let fidelityOnly = revised ? null : (a.fidelity_only || [])
if (revised) {
  phase('Korean')
  const ko = await agent(say(
    'Stage 11, the Korean edition. You are the translator.',
    `Write ${P}/ko/paper_ko.tex from ${ROOT}/tools/paper/template_ko.tex as a complete translation of ${P}/en/paper_en.tex, aligned paragraph by paragraph: the same "% id:" lines in the same order; per section the same \\label, \\ref, \\cite and \\qnum keys; the same \\input of ../common/ files; the Korean figures (figures/) and tables (tables/). The register is formal Korean academic prose; translate, never summarise. Translate the AI-assistance statement and the not-investment-advice note too.`,
    `Use the terms in ${ROOT}/tools/paper/glossary_ko.yaml, and add a term there when the paper needs one it lacks. Directly after \\qnum{...} and \\cite{...}, use the automatic particle commands of kotex (for example \\을 or \\는) instead of a fixed particle.`,
    `Run python -m tools.paper.consistency ${REL} and fix the Korean edition (never the English) until it exits 0, at most three attempts. Then compile with tools.paper.build.compile_tex(Path("${P}/ko/paper_ko.tex")) and fix every error it reports.`,
    `Commit ${REL}/ko/paper_ko.tex and, if it changed, tools/paper/glossary_ko.yaml.`,
  ), { label: 'translate-ko', phase: 'Korean', schema: STAGE })
  if (!ko || !ko.ok) return stop('korean', ko)
}
if (fidelityOnly === null || fidelityOnly.length) {
  phase('Korean')
  for (let pass = 1; pass <= 2; pass++) {
    st = await panelRound(k, fidelityOnly, true, `ko${pass}`, 'Korean')
    if (!st) return stop('fidelity', null)
    if (st.status !== 'BLOCKED_MAJOR' || pass === 2) break
    const fix = await agent(say(
      `Fidelity repair, pass ${pass}. You are the translator.`,
      `Read ${P}/review/fidelity_*.md. Fix every Major discrepancy in ${P}/ko/paper_ko.tex so that the Korean says exactly what the English says and claims no more than claims.yaml supports (the English is the reference and does not change here), and the Minor ones where they are right.`,
      `Rerun python -m tools.paper.consistency ${REL} until it exits 0, recompile with tools.paper.build.compile_tex(Path("${P}/ko/paper_ko.tex")), and commit ${REL}/ko/paper_ko.tex.`,
    ), { label: `fix-ko-${pass}`, phase: 'Korean', schema: STAGE })
    if (!fix || !fix.ok) return stop('korean', fix)
    revised = true
    fidelityOnly = null
  }
  if (st.status === 'BLOCKED_MAJOR') {
    return {
      status: 'BLOCKED_MAJOR', paper_id: PID, stage: 'fidelity', reset_at: resets, blockers,
      next: `The Korean edition still differs from the English after two fidelity passes. Show the owner ${REL}/review/fidelity_*.md.`,
    }
  }
}

// 12-13. Build, release record and STATUS (never RELEASED: only the owner's sign-off writes that)
if (revised) {
  phase('Build')
  const built = await agent(say(
    'Stage 12, the build and the release record.',
    `1. Run python -m tools.paper.build ${REL}. It must exit 0: fix the TeX (never a number, never a claim) and rerun, at most three attempts; otherwise ok=false with its errors. On success it writes ${REL}/en/build.json and ${REL}/ko/build.json (Tectonic version, bundle, font and PDF sha256).`,
    `2. Run python -m tools.paper.consistency ${REL} and python -m tools.paper.claims ${REL}. Put whatever problems they print in problems: they block release, so never hide them.`,
    `3. Write ${P}/meta.yaml with title_en, title_ko, abstract_en and abstract_ko (plain text; numbers as numbers.json formats them) and status_note: one sentence of scientific status (the claim labels, and the run qualification from MANIFEST.json, one of qualified, insufficient_data, smoke_only or not_run).`,
    `4. Commit ${REL}/en/paper_en.pdf, ${REL}/ko/paper_ko.pdf, ${REL}/en/build.json, ${REL}/ko/build.json, ${REL}/en/paper_en.tex, ${REL}/ko/paper_ko.tex and ${REL}/meta.yaml.`,
    'ok=true when the build exits 0, even if step 2 found problems.',
  ), { label: 'build', phase: 'Build', schema: STAGE })
  if (!built || !built.ok) return stop('build', built)
  blockers.push(...built.problems)
}
phase('Build')
const fin = await agent(say(
  'Final stage: the release state.',
  `1. Run python -m tools.paper.index gate ${REL} --round ${k}; status = the word it prints.`,
  `2. problems = what python -m tools.paper.consistency ${REL} and python -m tools.paper.claims ${REL} print, if either fails.`,
  `3. Commit ${REL}/review and ${REL}/STATUS.`,
  'Never write RELEASED: only the owner\'s sign-off does that, through python -m tools.paper.index release.',
), { label: 'final-status', phase: 'Build', schema: FINAL })
if (!fin) return stop('final-status', null)
blockers.push(...fin.problems)

const NEXT = {
  OWNER_REVIEW: `The owner reads both PDFs. Release only on the owner's sign-off sentence: python -m tools.paper.index release ${REL} --words "<the owner's words, verbatim>"`,
  REVIEW_INCOMPLETE: 'A reviewer returned nothing usable (reset_at names an exhausted quota). This is never "no objections": rerun after the reset with mode "rereview", or the owner records a substitution for that record in review/substitution.json.',
  BLOCKED_MAJOR: `Major issues remain; show the owner ${REL}/review/.`,
  DRAFT: 'No review record exists; run the write workflow again.',
  RELEASED: 'Already released.',
}
return {
  status: fin.status, paper_id: PID, round: k,
  pdfs: [`${P}/en/paper_en.pdf`, `${P}/ko/paper_ko.pdf`],
  reset_at: resets, blockers: [...new Set(blockers)], next: NEXT[fin.status],
}
