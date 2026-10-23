export const meta = {
  name: 'quantgen-paper-research',
  description: 'QUANTGEN research paper, part 1: scope, literature, reference and claim checks, integration analysis and the analysis protocol for one topic. Stops for the owner approval.',
  whenToUse: 'Started by the quantgen-paper skill for /quantgen-paper <topic>. Writes only papers/<paper_id>/ and changes no repository code.',
  phases: [
    { title: 'Scope', detail: 'split_map section 6 rows, modules with file:line, research questions' },
    { title: 'Literature', detail: 'blind searchers (canonical, 2023 to now, owner materials) and a completeness critic' },
    { title: 'Verify', detail: 'Crossref and arXiv records in refs.yaml; independent claim check' },
    { title: 'Integration', detail: 'how QUANTGEN implements the method, its gaps and guardrails' },
    { title: 'Protocol', detail: 'scope/protocol.md and scope/prereg.json' },
  ],
}

const a = args || {}
const ID = /^(fixture-)?(\d{4}-\d{2}-\d{2})-[a-z0-9]+(?:-[a-z0-9]+)*$/.exec(a.paper_id || '')
if (!a.topic || !ID || ID[2] !== a.today || !a.now_utc || !a.root) {
  throw new Error('args must be {topic, paper_id: "[fixture-]<today>-<slug>", today: "YYYY-MM-DD", now_utc, root}')
}
const ROOT = String(a.root).replace(/\\/g, '/').replace(/\/+$/, '')
const PID = a.paper_id
const P = `${ROOT}/papers/${PID}`
const FIXTURE = Boolean(ID[1])
const PRIVATE_OK = a.allow_private === true

const RULES = [
  `You are one stage of the QUANTGEN research-paper pipeline (spec: ${ROOT}/docs/superpowers/specs/2026-10-23-quantgen-split-and-paper-pipeline-design.md, section 5).`,
  `Repository root: ${ROOT}. Paper folder: ${P}. Paper id: ${PID}. Today: ${a.today}. Use absolute paths, run every python and git command with ${ROOT} as the working directory, and read and write text as UTF-8 with LF line endings.`,
  'Rules that bind this stage:',
  `- Write only inside ${P}. This workflow changes no repository code and commits nothing.`,
  '- Never edit paper_live/ or grokteam/; never run python -m paper_live.* or python -m grokteam.book; install nothing.',
  '- Never invent a reference, page, equation number, table or quotation. A source you could not open is reported as unread.',
  `- The owner's study materials (C:/Users/whydi/iCloudDrive/퀀트 학습 자료 and C:/Users/whydi/iCloudDrive/26년 2학기 수업자료) are private. Use them only to check derivations; the paper cites the published book or paper they follow, with pages. Never copy their text into any file, and never list them in refs.yaml${PRIVATE_OK ? ' except as class local_note, which the owner allowed for this paper' : ''}.`,
  FIXTURE ? '- This is the synthetic fixture paper of the pipeline dry run: keep every artefact minimal and do not open the owner study materials.' : '',
].filter(Boolean).join('\n')
const say = (...lines) => [RULES, ...lines].join('\n')

const LIST = { type: 'array', items: { type: 'string' } }
const STAGE = {
  type: 'object', required: ['ok', 'summary', 'problems'],
  properties: { ok: { type: 'boolean' }, summary: { type: 'string' }, problems: LIST },
}
const SCOPE = {
  type: 'object',
  required: ['ok', 'title', 'section6_rows', 'modules', 'questions', 'implemented', 'searchers', 'problems'],
  properties: {
    ok: { type: 'boolean' },
    title: { type: 'string' },
    section6_rows: { type: 'array', items: { type: 'integer' } },
    modules: {
      type: 'array',
      items: { type: 'object', required: ['path', 'lines', 'role'], properties: { path: { type: 'string' }, lines: { type: 'string' }, role: { type: 'string' } } },
    },
    questions: LIST,
    implemented: { type: 'string', enum: ['yes', 'partial', 'no'] },
    searchers: { type: 'array', items: { type: 'string', enum: ['canonical', 'recent', 'owner_materials'] } },
    problems: LIST,
  },
}
const REF = {
  type: 'object', required: ['key', 'type', 'authors', 'year', 'title', 'class', 'why'],
  properties: {
    key: { type: 'string' }, type: { type: 'string' }, authors: LIST, year: { type: 'integer' }, title: { type: 'string' },
    venue: { type: 'string' }, volume: { type: 'string' }, pages: { type: 'string' },
    doi: { type: 'string' }, arxiv: { type: 'string' }, url: { type: 'string' },
    class: { type: 'string', enum: ['published', 'working_paper', 'book'] }, why: { type: 'string' },
  },
}
const FOUND = { type: 'object', required: ['refs', 'notes_file'], properties: { refs: { type: 'array', items: REF }, notes_file: { type: 'string' } } }
const GAPS = { type: 'object', required: ['gaps'], properties: { gaps: LIST } }
const CLAIMS = {
  type: 'object', required: ['ok', 'supported', 'unread', 'unsupported', 'problems'],
  properties: { ok: { type: 'boolean' }, supported: { type: 'integer' }, unread: { type: 'integer' }, unsupported: { type: 'integer' }, problems: LIST },
}
const SUMMARY = {
  type: 'object', required: ['ok', 'summary_md', 'proposed_code', 'problems'],
  properties: { ok: { type: 'boolean' }, summary_md: { type: 'string' }, proposed_code: LIST, problems: LIST },
}
const stop = (stage, r) => ({ status: 'STOPPED', paper_id: PID, stage, problems: r ? r.problems : [`the ${stage} agent returned nothing`] })

// 1. Scope
phase('Scope')
const scope = await agent(say(
  `Stage 1 of 5, Scope. Topic: ${JSON.stringify(a.topic)}.`,
  `1. If ${P} already exists, stop: ok=false, problems=["${P} already exists"]. Otherwise create ${P}/scope/.`,
  `2. Read ${ROOT}/research_notes/QUANTGEN TRADEGEN split map/split_map.md sections 6 and 8.6. Map the topic to its section 6 rows, then find the modules that implement it; give file:line ranges only for code you opened and read.`,
  `3. Write ${P}/scope/questions.md: the topic, a working title, the section 6 rows, a module table (path, lines, role), three to six research questions, and whether QUANTGEN already implements the method (yes, partial or no) with the evidence.`,
  '4. Choose the literature searchers the topic needs: canonical (origin papers and the textbook treatment), recent (the state of the art from 2023 to now), owner_materials (derivation checks against the owner study materials). Leave one out when the topic does not need it, and say why in questions.md.',
  `5. Write ${P}/.gitignore with one pattern per line: study/cache/, *.aux, *.log, *.blg, *.bbl, *.out, *.toc, *.xdv, *.synctex.gz, qgpaper.sty.`,
  `6. Run python -m tools.paper.index gate ${P} (with no review records it writes STATUS = DRAFT).`,
), { label: 'scope', phase: 'Scope', schema: SCOPE })
if (!scope || !scope.ok) return stop('scope', scope)

// 2. Literature: blind searchers, a completeness critic, one gap-filling search, a merge
phase('Literature')
const BRIEFS = {
  canonical: 'Find the origin literature and the standard treatment: the paper or papers that introduced the method, its key extensions, and one or two graduate textbooks (chapter and pages).',
  recent: `Find the state of the art from 2023 to ${a.today}: refereed journals; NBER, Federal Reserve, BIS, ECB, Bank of England and IMF working papers; arXiv q-fin; SSRN. Keep a working paper and its published version as two separate entries and say which is which.`,
  owner_materials: `Read the owner study materials (read-only) for the derivations the topic needs. Write ${P}/scope/derivations.md: for each derivation, what you checked, the published book or paper the material follows (authors, title, edition, pages) and whether the derivation agrees. Name the material files there but copy none of their text. Return only the published sources as refs.`,
}
const searchers = scope.searchers.filter(s => !(FIXTURE && s === 'owner_materials'))
const notesFile = s => (s === 'owner_materials' ? `${P}/scope/derivations.md` : `${P}/scope/lit_${s}.md`)
const search = (s, brief) => agent(say(
  `Stage 2 of 5, Literature: searcher "${s}". You are blind to the other searchers: work from ${P}/scope/questions.md only and open no other scope/lit_*.md file.`,
  brief,
  'Use web search and page fetches for public sources. Every entry must be a real work you located (DOI, arXiv id, or a publisher or library page). Give the DOI or arXiv id whenever one exists. key = first author surname + year + first title word, lowercase ASCII (for example bollerslev1986generalized). class is published, working_paper or book.',
  `Write your notes (what each source contributes, with chapter, page, equation or table locators) to ${notesFile(s)} and return the entries.`,
), { label: `search-${s}`, phase: 'Literature', schema: FOUND })
const found = (await parallel(searchers.map(s => () => search(s, BRIEFS[s])))).filter(Boolean)
const listing = rs => rs.map(r => `- ${r.key}: ${r.authors.join(', ')} (${r.year}), ${r.title}${r.venue ? ', ' + r.venue : ''}`).join('\n')
const critic = await agent(say(
  `Stage 2 of 5, Literature: completeness critic. The research questions are in ${P}/scope/questions.md. The blind searchers returned:`,
  listing(found.flatMap(f => f.refs)) || '(nothing)',
  'List what is missing for a journal-quality literature review of this topic: an origin paper, a canonical extension, a result from 2023 to now that changes the picture, the published version of a working paper, a textbook derivation. Each gap is one specific, searchable item. Return an empty list when nothing material is missing. Do not search and do not write files.',
), { label: 'literature-critic', phase: 'Literature', schema: GAPS })
if (!critic) log('The completeness critic returned nothing: the literature was not checked for gaps.')
if (critic && critic.gaps.length) {
  const fill = await search('gaps', `Close exactly these gaps and nothing else:\n${critic.gaps.map(g => '- ' + g).join('\n')}`)
  if (fill) found.push(fill)
}
const pool = found.flatMap(f => f.refs)
if (!pool.length) return stop('literature', { problems: ['no searcher returned a reference'] })
const merged = await agent(say(
  'Stage 2 of 5, Literature: merge.',
  `1. Merge the entries below into ${P}/refs.yaml, the single source of bibliography truth (schema in ${ROOT}/tools/paper/refs.py): drop duplicates (same DOI, arXiv id or title), keep working papers apart from their published versions, and keep only entries the review uses.`,
  JSON.stringify(pool),
  `2. Write ${P}/scope/literature.md from the notes in ${P}/scope/lit_*.md: the origin of the method, its development and the state of the art, as an outline of the literature section. Number its planned paragraphs literature-1, literature-2, ... and list under each the claims it will make and the refs keys that support them.`,
  `3. Write ${P}/claims.yaml: one row per (claim, source) of literature.md with id (C1, C2, ...), paragraph_id (the planned literature-<n>), source_key, locator (page, equation or table), support (empty for now) and status unread.`,
  `4. Write ${P}/refs.bib with tools.paper.refs: write_bib(load_refs(refs.yaml), refs.bib).`,
), { label: 'literature-merge', phase: 'Literature', schema: STAGE })
if (!merged || !merged.ok) return stop('literature', merged)

// 3. Verification of references, then an independent claim check
phase('Verify')
const verified = await agent(say(
  'Stage 3 of 5, reference verification.',
  `1. Read ${ROOT}/tools/paper/refs.py. Run its verify_file on ${P}/refs.yaml with now_utc="${a.now_utc}" and its network fetch (Crossref api.crossref.org/works/<doi> for DOIs, export.arxiv.org/api/query?id_list=<id> for arXiv ids). It writes a verified record (method, url, retrieved_utc, fetched_title, ok) on every entry.`,
  '2. Entries it cannot reach (SSRN often blocks robots; books have no DOI) are method manual: open a publisher, library or SSRN page yourself, and set ok true only when that page shows the same title, authors and year; record the url and the title you saw.',
  `3. An entry whose fetched title does not match is a wrong reference: correct it from the source, or remove it together with every claims.yaml row and literature.md mention that uses it.`,
  `4. Regenerate ${P}/refs.bib and run verify_file once more. ok=true only when it reports no problems; otherwise return them.`,
), { label: 'refs-verify', phase: 'Verify', schema: STAGE })
if (!verified || !verified.ok) return stop('verify', verified)
const claims = await agent(say(
  'Stage 3 of 5, independent claim check. You did not write these claims; check them as a sceptical reader.',
  `For every row of ${P}/claims.yaml, open the source (DOI landing page, arXiv PDF, publisher preview; for a book, its own pages if you can open them, or the derivation note in ${P}/scope/derivations.md) and read the passage at the locator.`,
  '- If it supports the claim: status supported, and support = the supporting passage (at most 25 quoted words) or the derivation step, with the exact locator.',
  '- If it does not: status unsupported, and say why in support.',
  '- If you could not open the passage: leave status unread. Never mark a row supported from memory.',
  'Return the counts. ok=true when you checked every row; unread rows are allowed here, and they block release later.',
), { label: 'claims-check', phase: 'Verify', schema: CLAIMS })
if (!claims || !claims.ok) return stop('claims', claims)

// 4. Integration analysis
phase('Integration')
const integ = await agent(say(
  'Stage 4 of 5, integration analysis. Read the code; change none of it.',
  `Write ${P}/scope/integration.md: how QUANTGEN implements the method today (file:line for every statement, starting from ${P}/scope/questions.md and your own reading); where it departs from the literature in ${P}/scope/literature.md; its gaps; and its guardrails: the acceptance tests that cover it, by name; the read-only and isolation guards T-RO-01 and T-CTX-01; and whether the frozen studies GROKTEAM-BOOK or paper_live H2 depend on it (they run only from the tag studies-of-record-2026-10-23). If the method is not implemented, say what new code it would need and where.`,
), { label: 'integration', phase: 'Integration', schema: STAGE })
if (!integ || !integ.ok) return stop('integration', integ)

// 5. Analysis protocol and pre-registration
phase('Protocol')
const protocol = await agent(say(
  'Stage 5 of 5, the analysis protocol.',
  `1. Write ${P}/scope/protocol.md with these headings, each filled in: Estimand; Observation unit; Sample and eligibility; Data access history (has this series been used before in ${ROOT}/docs or ${ROOT}/research_notes? name the files); Holdout (dated after the freeze wherever a claim is confirmatory); Leakage controls; Dependence correction; Power and minimum detectable effect; Multiplicity; Variants to be tried (every one, listed now); Claims and labels (each claim labelled exploratory, pre-specified on historical data, or confirmatory on a post-freeze holdout); Status propagation (a NOT_RUN, smoke-only or insufficient-data result is never a positive claim, and its status is carried to the abstract, the conclusion and the index); QUANTGEN gates used, and where a gate does not fit the topic (for example the 5-year strategy gate) and why; Proposed new code (each module with the guards it must pass: the T-RO-01 order-path scan, the T-CTX-01 isolation scan, tests/flet_api_guard.py for ui/, the test_s4 rules for core/engine, lazy registration in tests/run_all.py).`,
  `2. Write ${P}/scope/prereg.json: {"paper_id": "${PID}", "created_utc": "${a.now_utc}", "run_kind": "exploratory" or "prespecified" or "confirmatory" (the strongest label any claim carries), "seed": <integer>, "protocol_sha256": <sha256 of scope/protocol.md as written>, "claims": [{"id", "label", "estimand", "test", "alpha"}], "variants": [...], "holdout": {"start", "end"} or null, "pinned_code": {<repository-relative path>: <sha256 of the file now>} for every existing module the study will call ({} when none; tools.paper.study.start_run refuses a prereg without this key), "new_code": [<repository-relative paths the protocol proposes>], "ledger_family": "PAPER-${PID}"}.`,
  '3. Return summary_md: one screen for the owner with the title, the research questions, whether QUANTGEN implements the method, the references (verified, manual, problems), the claims (supported, unread, unsupported), the claim labels, the holdout, and the proposed new code with its guards. proposed_code = the new_code list.',
), { label: 'protocol', phase: 'Protocol', schema: SUMMARY })
if (!protocol || !protocol.ok) return stop('protocol', protocol)

return {
  status: 'AWAITING_APPROVAL',
  paper_id: PID,
  paper_dir: P,
  title: scope.title,
  claims: { supported: claims.supported, unread: claims.unread, unsupported: claims.unsupported },
  proposed_code: protocol.proposed_code,
  summary_md: protocol.summary_md,
  next: `Owner approval in chat, then: python -m tools.paper.approval approve papers/${PID} --words "<the owner words, verbatim>"; commit papers/${PID}; then /quantgen-paper write ${PID}.`,
}
