# SOP — how a result gets handed off

`COLLABORATION.md` says how we work together. `business/SCOPE_AND_BRANCHES.md` says who owns what.
This says how a finished result crosses between us, so neither of us is ever blocked waiting on the
other.

Every rule below was bought by something that actually went wrong in the week of 26 July – 2 Aug.
None of it is generic best practice.

---

## 1. Definition of done

A result is **not** done when the number exists. It is done when the other founder can clone the
repo and get the same number without asking a question.

Checklist, all five:

- [ ] The number is written to a **machine-readable artifact** (`*.json` / `*.csv`), not only to a
      report, a paper, or a message.
- [ ] The **script that produced it** is committed next to the artifact.
- [ ] Every **input** the script reads is committed too.
- [ ] The number ships with its **dumb baseline** (§3).
- [ ] A **logbook entry** exists (§4) and a **tag** points at the commit (§5).

> **Why.** The CrystalScore simulatability term for CRYSTAL-1 was quoted as `0.92` in both papers
> for weeks. It had never been computed into any artifact — there was no script, no JSON, nothing to
> re-run. It looked finished because it was written down.

---

## 2. Reproduce from a clean clone before you call it done

Run the check on a fresh clone, not on your working copy. Your working copy has files you
regenerated locally and forgot you regenerated.

```bash
git clone <repo> /tmp/repro && cd /tmp/repro
python <the script>          # must produce the same numbers
```

> **Why.** CrystalScore reproduced end-to-end on one side — but only because five of its inputs had
> been regenerated locally there. From a clean clone it would have failed. The pipeline looked reproducible
> from inside the one environment where it wasn't being tested.

---

## 3. Every number ships with its dumb baseline

Report the **lift over the dumbest model that could produce that number**, never the raw figure
alone. If the two sides of a comparison use different scales, say so and give the like-for-like form.

| kind of claim | the dumb baseline you must report |
|---|---|
| classification / agreement | majority class |
| prediction | constant, or the target's own lagged value |
| policy improvement | do-nothing, and an exposure-matched twin |
| "the tree explains the policy" | an order-*k* Markov model on the action's own past |

> **Why, twice.** The 8-leaf tree reproduces the DP champion table at `0.932` — but majority class
> alone gets `0.807`, so the honest lift is `+0.125`. And R6c's simulatability is `1 − SS_res/SS_tot`
> (chance-corrected, constant → 0) while CRYSTAL-1's was raw accuracy (constant → 0.807): the paper's
> headline `0.15 → 0.92` compared two different scales. Earlier, raw weight completeness `0.34`
> turned out to be ~28× dominated by gross exposure. Three instances, one rule.

---

## 4. Logbook entry — name the verdict, never the question

Append to `EXPERIMENT_LOGBOOK.md`. Use the existing fields:

```
### <ID> · <date> · <TITLE = WHAT WE FOUND>
- **Who / agent:**
- **Track:**
- **Question:**
- **Setup:**
- **Command:**            → **artifact:** <path>
- **Result:**
- **Null tested:**
- **Honest caveat:**
- **Verdict:** CONFIRMED | NULL | KILLED | OPEN
- **Figure:**
- **Follow-up:**
```

**The title states the outcome.** `"G12 — return and legibility in strict tension (NULL)"`, not
`"G12 certified legibility-raising rule"`. If the entry is a null, the word appears in the title.

> **Why.** E-04's title, its `experiment` field inside the JSON, and its line in `HL_VERSION_MAP.md`
> all read "certified legibility rule." The result was `n_certified_legibility_moves: 0` — a
> certified null. All three strings named the question. A week of work was planned around
> reproducing a rule that does not exist.

---

## 5. Tagged snapshot — the handoff unit

When a result is done, tag it. The tag, not a message, is what the other person pulls.

```bash
git tag -a <exp-id>-<slug>-snapshot -m "<what it is>

Frozen gate:  <path>  <hash here>  <hash in mothership>
Entry point:  python <script>
Artifacts:    <paths>
Config:       <seeds, budgets, windows>
Verdict:      <the outcome, in one line>"
git push origin main --follow-tags
```

The tag message must carry the **gate hash**, so "which firewall was this judged by" is never a
question. Name the gate explicitly — for G12 it is `src/hl/pareto_gate.py`, not `hl_gate_eval.py`.

---

## 6. Where things live

Repositories are held in the shared organisation **[`API-Capital`](https://github.com/API-Capital)**,
with both founders as organisation **Owners** — not as admins on individual repos. Owner is the org
role that carries co-ownership; repo-admin does not. The org becomes a company asset at
incorporation.

| repo | what it is | status |
|---|---|---|
| `API-Capital/self-evolving-trading-bot` | the mothership — full history, both tracks, all live work; this is where day-to-day commits land | to transfer |
| `API-Capital/CrystalRL` | interpretability extract — clone-and-run | transferred |
| `API-Capital/Hello-CrystalRL` | public evidence slice | to transfer |

An artifact needed to reproduce an interpretability result belongs in **CrystalRL**, not only in the
mothership. Mirror it in the same commit that produces it.

> **Why.** Five CrystalScore inputs lived only in the mothership. Nobody noticed until someone tried
> to run the pipeline from the other repo.

**Move a repo by transfer, never by re-upload.** GitHub's *Settings → Danger Zone → Transfer
ownership* keeps the full commit history, the tags, the issues, and leaves a redirect from the old
URL so existing links and clones keep working. Pushing a snapshot into a fresh repo keeps none of
that.

> **Why.** The first copies placed in the org were snapshot uploads: 4 commits against the source's
> 35, no tags, and a commit graph with no ancestor in common — so the two could not even be merged
> normally. Anyone starting from the org copy would have silently got a state that was a week stale
> and missing the snapshot tag.

**One canonical remote per repo.** When a repo moves, the old location stops receiving pushes the
same day. Two writable copies of the same project is the failure this section exists to prevent.

---

## 7. When you are blocked

Do not wait for the weekly call.

1. Message the other founder with the **exact paths** you need and what you are blocked on.
2. Owner responds within **24 hours** — either the commit, or a date.
3. If no answer in 24 hours, say so at the Sunday call and proceed on a local copy, flagged as
   unverified.

> **Why.** One of us was blocked on the codebook and the steering curve for several days, on a task
> that took twenty minutes once asked.

---

## 8. Amending something already shipped

If a number in a paper, a report, or a slide turns out to be wrong or unsupported: **amend it in the
same session you find it**, and say so in the logbook entry. Do not carry it to the next meeting.

Retractions are normal here. Six evaluation harnesses have been invalidated and zero conclusions
were lost because of it — the record is what makes the surviving results worth anything.
