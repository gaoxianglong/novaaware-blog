> Original publication: June 2026

# AI-Testing Series (Part 1) — How to Use AI to Quickly Build API Test Automation

## I. Background
Earlier this year, our team took on a cross-domain initiative spanning multiple systems. We owned the middle-platform component: 100+ APIs, two environments, and test results due within one week. The old way meant half a day just to scaffold folders, write BaseClient, wire pytest and Allure, then manually align cases with data. This time we treated the AI Agent as a pair-programming test architect: from repo skeleton to the first green test took about two hours. This article turns that run into a reusable playbook you can adopt on your team.


**In depth — Why “hand-built scaffolding” no longer keeps up**
The traditional path is familiar: read API docs → define layers → write HTTP wrappers → add assertion helpers → patch conftest → copy cases one by one. The bottleneck is not typing speed but context switching — you must hold env var names, business error codes, auth patterns, and data dependency chains in your head. Miss one layer and everything downstream is rework.

The AI Agent model is different: humans set constraints and acceptance criteria; the Agent runs a closed loop in the repo — read code → edit files → run commands → read errors → fix again. You are no longer “the person who writes every line of framework code”; you are the product owner of the framework.

| Dimension | Traditional build | AI-Agent build |
| --- | --- | --- |
| Scaffold | Copy from old repo / wiki | Agent generates from AGENTS.md + conventions |
| API client | Manual per endpoint | Agent reads OpenAPI / sample curl, emits *API classes |
| Test data | Spreadsheet → hand paste | Agent extracts to testdata/*.py or JSON |
| Debug loop | You run pytest locally | Agent runs pytest, parses traceback, patches |
| Knowledge | Tribal knowledge in chat | Rules + skills persisted in ./rules |


## II. Building the automation framework with an AI Agent

### 1. Three "hard inputs" before the Agent starts
An Agent is not magic. Without inputs it will invent base_url. Before kickoff, prepare these three items in a FRAMEWORK_SPEC.md:

- Tech stack contract: Python 3.10+, pytest, requests, allure-pytest; data-driven style (JSON / Python dict).
- Layering convention: e.g. apiauto/api (protocol), apiauto/common (client & data driver), cases/ (business tests), testdata/ (static payloads).
- One golden-path case: pick the simplest, best-documented API (e.g. a GET query), attach a real request sample and expected errorCode.

With a spec in place, the first Agent prompt can be concrete — not vague lines like "build me an automation framework."


### 2. Framework build — seven-step closed loop
![Figure 1](../imgs/apitestautomation1.png)

The steps below are Agent tasks you can execute, not keyboard work you do yourself.


**Step 1: Lock non-negotiable rules**
Put project-level rules under ./rules, for example:

```
# All HTTP traffic must go through BaseApiClient; raw requests.get (or other direct requests calls) are not allowed in test cases.
# Assert business response codes first (errorCode / code), then HTTP status (e.g. 200).
# Sensitive tokens may appear only in testdata; never commit real production secrets.
```

Then tell the Agent:

```
Read existing apiauto/common/base_client.py if any; otherwise create BaseApiClient with Session reuse, retry on 5xx, and safe JSON parse. Match typing style in repo.
```

The Agent scans the repo and matches existing style instead of dropping a generic template. Acceptance for this step: python -c "from apiauto.common.base_client import BaseApiClient" imports cleanly.


**Step 2: Let the Agent generate the directory skeleton (do not copy an old project)**
Teams often clone an entire cases/ tree from another line of business and inherit dead code. The Agent approach should ask for a minimal runnable tree:

```
project-root/
├── apiauto/
│   ├── api/           # *API classes
│   ├── common/        # client, data driven, templates
│   └── case/          # smoke tests
├── cases/             # domain test suites
├── testdata/          # static payloads
├── conftest.py        # fixtures, env, markers
├── pytest.ini
└── requirements.txt
```

Prompt example (English prompts tend to be more stable for Agents):

```
Create minimal pytest layout per FRAMEWORK_SPEC.md.
Add pytest.ini with markers: smoke, regression, P0.
Add conftest.py: env switch QA/STAGE via ENV variable.
Do not create empty placeholder packages without __init__.py.
```

After generation, your job is one thing: review the diff, delete extra folders — still faster than mkdir from scratch.


**Step 3: Protocol layer — from curl / Swagger to API Facade**
Paste API docs or one real curl to the Agent and constrain the output:

```
Generate GrabBookAPI extends BaseApiClient:
- method grab_book(**kwargs) -> dict
- base_url from os.environ["TRADE_HOST"]
- docstring lists required business fields
```

Typical Agent output matches a thin-wrapper pattern: URL + body assembly only; assertions stay in the case layer.

Manual checkpoints (required):

| Check item | Pass criteria |
| --- | --- |
| URL join | Relative path works with base_url |
| Idempotency | POST body not mutated across retries |
| Auth header | Token read from fixture, not hardcoded in API class |

---

<p align="center">
  <a href="https://novaaware.com">
    <img src="../../imgs/image-ENG.png" alt="NovaAware — novaaware.com" width="600"/>
  </a>
</p>

<p align="center"><sub><i>Tired of pulling out nails one by one? <a href="https://novaaware.com"><b>NovaAware</b></a> handles the model-and-agent plumbing for you — so you can stop fighting proxies and get back to your own business.</i></sub></p>

---

**Step 4: Data-driven layer — Agent batch-builds testdata**
Roughly 60% of API automation time goes to data maintenance. Give the Agent Swagger examples or captured JSON:

```
For endpoint getRefundMerchant:
1. Create testdata/getRefundMerchant_data.py with one happy-path dict.
2. Add parametrize wrapper in cases/refund_core/test_getRefundMerchant.py
3. Use pytest.mark.smoke on happy path only.
```

The Agent can emit a Python dict (few fields) or JSON + generic_data_driven (many named cases). Your project may already follow a similar layout:

```python
# testdata shape (example)
getMerchant = {
    "mid": "...",
    "orderSerialNo": "210089202501011320266400",
    # ...
}
```

Note: Have the Agent move traceId, ts, etc. to @pytest.fixture dynamic values to avoid flaky stale-parameter failures — encode this in Rules.


**Step 5: First green test — Agent brings its own debug loop**
This step differs most from traditional setup. Tell the Agent:

```
Run: pytest cases/refund_core/test_getRefundMerchant.py -v --tb=short
Fix failures until green. Do not weaken assertions.
```

The Agent adjusts hosts, field names, and headers based on tracebacks until the test turns green. Humans usually intervene only in three cases:

- (1) VPN / whitelist — Agent cannot reach the env; you confirm network access.
- (2) Real business IDs — e.g. order numbers from the test data platform; you update the spec.
- (3) Product defects — log the bug; mark xfail for now.

For Allure, add:

```
Add @allure.feature / @allure.story decorators consistent with service name.
Ensure pytest --alluredir=./allure-results works in CI.
```


**Step 6: CI and quality gates — Agent drafts pipeline, human approves permissions**
Have the Agent draft a minimal pipeline from existing CI (GitHub Actions / Jenkinsfile):

```yaml
# Conceptual CI pipeline — review secrets after Agent output
stages:
  - lint (ruff/flake8)
  - test (pytest -m smoke)
  - report (allure upload)
```

What humans must review:

| Artifact | Agent can draft | Human must approve |
| --- | --- | --- |
| requirements.txt | Yes | Pin versions for prod-like env |
| Secrets / tokens | Never commit | Use CI secret store |
| Parallel workers | Suggest pytest -n auto | Rate limit against shared QA |
| Failure retry | Add flaky retry plugin | Cap retries to avoid masking bugs |


**Step 7: Capture Skills — turn wins into reusable instructions**
After the framework stands, document "add one API test case" as a Skill (or team SKILL.md), e.g.:

```
Provide API path + method + sample response
Generate *API + testdata + test_*.py
Open a PR only after the single-file pytest run passes locally.
```

New hires can @skill api-case-scaffold instead of re-teaching layering to the Agent.


### 3. What the AI-generated target framework looks like

Post-Agent layering matches a mature data-driven framework; generation is simply an order of magnitude faster.

![Figure 2](../imgs/apitestautomation2.png)

**Data-driven call chain**

![Figure 3](../imgs/apitestautomation3.png)


## III. Lessons and tips

### 1. Prompt strategy — directing the Agent like a senior TL
Three field lessons:


**Constraints before features**
Bad prompt: "Write refund API tests."

Good prompt: "Add tests under cases/refund_core/; no new raw requests; assert errorCode==\"0000\"; data in testdata/."


**Expand one layer at a time**
Do not ask for "scaffold + 20 cases + Jenkins" in one message. Accept each layer, then start a fresh Agent session — otherwise the diff is unreviewable.


**The repo is the source of truth**
Always add: Read neighboring files and match naming conventions.

The Agent's guess on whether your team uses order_No or orderNo beats any generic tutorial.


### 2. Common failures and fixes
| Symptom | Root cause | Fix |
| --- | --- | --- |
| All green locally, still fails in prod | Only assert HTTP 200 | Rule: must assert all business codes |
| Hard-coded timestamps in data | Agent copied the sample | Dynamic fixtures in conftest |
| Bloated API classes | Assertions inside API | Require: API calls only; assert in cases |
| Reinventing utilities | Agent did not search first | First prompt line: Search repo before create |
| Secrets in Git | No pre-commit hook | detect-secrets + human PR scan |


### 3. Go-live checklist
Self-check before handoff — avoid "demo runs, cannot maintain":

| # | Item | Status |
| --- | --- | --- |
| 1 | pytest -m smoke passes on a clean env | ☐ |
| 2 | No raw requests; all via BaseApiClient | ☐ |
| 3 | No production secrets in testdata | ☐ |
| 4 | Failure logs expose requestId/traceId | ☐ |
| 5 | Allure groups by feature | ☐ |
| 6 | CI runs smoke; full suite nightly | ☐ |
| 7 | ./rules or SKILL documents the SOP for adding new API test cases. | ☐ |


## IV. Closing
Building API automation with an AI Agent splits architecture decisions from implementation grunt work: you write the spec and acceptance; the Agent closes the loop in the repo. Remember the seven steps — Rules → skeleton → Client → API → data → green test → CI/Skill. Technically you still need layering, business assertions, and data isolation — Agent-generated code does not make those correct by default.

**Working alongside traditional setup**

The Agent does not replace test engineers; it absorbs mechanical work. Suggested split:

- Human: spec, env strategy, business assertion policy, PR review, exploratory scenarios
- Agent: scaffold, Client/API templates, bulk testdata, pytest fix loops, docs and SKILL
- Human + Agent: complex flows (order → pay → refund) — Agent drafts; human adds state machine and teardown

A "complete" framework means switchable envs, data-driven cases, reporting, CI gates, and extensible cases — Agent can draft these in hours; you spend remaining time on edge cases, for a much higher overall ROI.

If this helped, feel free to like and save. Questions are welcome in the comments.

Attribution: NovaAware Team — original work; all rights reserved.

---

<p align="center">
  <a href="https://novaaware.com">
    <img src="../../imgs/image-ENG.png" alt="NovaAware — novaaware.com" width="600"/>
  </a>
</p>

<p align="center"><sub><i>Tired of pulling out nails one by one? <a href="https://novaaware.com"><b>NovaAware</b></a> handles the model-and-agent plumbing for you — so you can stop fighting proxies and get back to your own business.</i></sub></p>

---