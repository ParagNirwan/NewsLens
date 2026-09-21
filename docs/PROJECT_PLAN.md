# NewsLens — AI News Research & Fact-Checking Agent

## 1. Project Vision

NewsLens is an AI-powered research agent that investigates news questions and factual claims.

A user asks a question such as:

> "Did X cause Y?"

or:

> "What happened with the latest German migration legislation?"

The agent does not simply generate an answer from its internal knowledge. It performs an investigation:

1. Understand the user's question.
2. Break the question into research tasks.
3. Search for relevant news coverage.
4. Retrieve and read useful sources.
5. Identify claims, disagreements, and missing evidence.
6. Search for primary sources when appropriate.
7. Cross-check important claims.
8. Distinguish established facts from interpretation, disputed claims, and uncertainty.
9. Produce a structured report with citations.
10. Stop when it has sufficient evidence.

The project should demonstrate genuine agentic behaviour rather than being a normal chatbot.

Core mental model:

    Goal
      ↓
    Decide
      ↓
    Act
      ↓
    Observe
      ↓
    Update State
      ↓
    Decide ...
      ↓
    Finish


## 2. Important Design Principle

Do NOT define the project as:

    "Find one left-wing source and one right-wing source and decide who is correct."

Political labels are often subjective and can oversimplify sources.

Instead, NewsLens should support source diversity while separating different source roles:

- Primary sources
  - Government documents
  - Parliament documents
  - Court decisions
  - Official statistics
  - Original research
  - Official statements

- News sources
  - Different outlets and editorial perspectives

- Analysis
  - Academic research
  - Think tanks
  - Expert analysis

The system should explicitly distinguish:

- Established facts
- Claims made by sources
- Interpretations
- Disputed claims
- Causal claims
- Missing evidence
- Uncertainty

The agent should not manufacture certainty when sources disagree.


## 3. Target Architecture

Initial architecture:

    User
      |
      v
    React UI
      |
      v
    Python API / Agent Service
      |
      +----------------------+
      |                      |
      v                      v
    LLM                 Web Search Tool
      |                      |
      +----------+-----------+
                 |
                 v
             Web Pages
                 |
                 v
           Source Extraction
                 |
                 v
             Agent State
                 |
                 v
           Final Report
                 |
                 v
             React UI


Later architecture:

    React
      |
      v
    FastAPI
      |
      v
    Agent Orchestrator
      |
      +---- LLM Provider
      |
      +---- Search Tool
      |
      +---- Page Reader
      |
      +---- Source Analyzer
      |
      +---- Claim Extractor
      |
      +---- Primary Source Finder
      |
      +---- Evidence Store
      |
      +---- Evaluation System
      |
      v
    PostgreSQL


## 4. Recommended Technology Stack

### Programming Language

Python 3.12+

Reason:

- Excellent AI ecosystem.
- Fast to prototype.
- Large number of LLM and web-research libraries.
- Lets us focus on agent concepts instead of framework complexity.

### Backend

FastAPI

Responsibilities:

- HTTP API
- Research request handling
- Authentication later if needed
- Streaming agent events to frontend
- Returning structured research reports

### Frontend

React + TypeScript

Responsibilities:

- Research input
- Agent activity / live execution trace
- Source list
- Claim/evidence display
- Final report
- Research history

### Database

PostgreSQL

Initially optional.

Later use it for:

- Research sessions
- Agent state
- Sources
- Claims
- Evidence
- Reports
- Evaluation results
- User history

### Containers

Docker + Docker Compose

Services eventually:

- frontend
- backend
- PostgreSQL


## 5. LLM

Start with one hosted LLM provider.

The application should hide provider-specific code behind a small abstraction so the model can be changed later.

Potential providers:

- OpenAI
- Anthropic
- Google
- Local models later

Do not start by supporting multiple providers.

First make one provider work reliably.

LLM responsibilities:

- Understand research goal.
- Decide which tool to use.
- Generate tool arguments.
- Interpret tool results.
- Decide whether more research is needed.
- Extract structured claims.
- Produce final report.


## 6. Agent Framework Strategy

Do NOT start with LangChain, CrewAI, AutoGen, or a large agent framework.

First implement the basic agent loop ourselves.

Concept:

    while not finished:

        decision = LLM(state, available_tools)

        if decision == tool_call:
            result = execute_tool(decision)
            state.add(result)

        elif decision == final_answer:
            finish


After understanding the fundamentals, evaluate an orchestration framework.

Possible later options:

- LangGraph
- PydanticAI
- Semantic Kernel
- Other production agent frameworks

The framework should solve a problem we actually have, not be added just because it is popular.


## 7. Initial Tools

Version 0.1 should have very few tools.

### Tool 1: search_web

Input:

    query: string

Output:

    title
    url
    snippet
    source/domain
    publication date if available

Purpose:

Allow the agent to discover relevant sources.

### Tool 2: open_page

Input:

    url: string

Output:

    page title
    cleaned text
    metadata
    links if useful

Purpose:

Allow the agent to inspect a source rather than relying only on search snippets.

### Tool 3: extract_claims

Initially this can be an internal structured LLM operation rather than a separate external tool.

Output:

    claim
    source
    claim_type
    supporting_text
    confidence/uncertainty


## 8. Agent Loop

The first real agent should work approximately like this:

    User:
    "Did X cause Y?"

              |
              v

    Analyze Goal
              |
              v
    Decide research query
              |
              v
    search_web()
              |
              v
    Observe results
              |
              v
    Select useful sources
              |
              v
    open_page()
              |
              v
    Extract claims
              |
              v
    Are important claims sufficiently supported?
          /                    \
        NO                      YES
        |                        |
        v                        v
    Search again            Build report
        |
        +---------> Agent Loop


## 9. Agent State

The agent needs state.

Example:

    ResearchState

    {
        goal,
        sub_questions,
        searches,
        sources,
        claims,
        evidence,
        disagreements,
        primary_sources,
        unresolved_questions,
        actions_taken,
        iteration_count,
        final_report
    }

This state is what allows the agent to remember what it has already done.

Important:

The LLM itself should not be treated as the database.

The application owns the state.


## 10. Source Model

Each source should eventually contain:

    Source

    id
    url
    title
    publisher
    author
    publication_date
    retrieved_at
    source_type
    text
    credibility_notes
    political/editorial characterization if available
    claims


Possible source_type values:

    PRIMARY
    NEWS
    ANALYSIS
    ACADEMIC
    OFFICIAL
    UNKNOWN


Do not automatically treat a source's political/editorial orientation as a statement of truth or falsehood.


## 11. Claim Model

A research report should break important statements into claims.

Example:

    Claim:

    "Unemployment increased by 4%."

    Evidence:

    Official statistics.

    Status:

    Supported


Another:

    Claim:

    "Immigration caused the increase."

    Evidence:

    Sources disagree and available statistics alone do not establish causation.

    Status:

    Not established / disputed


Possible claim status:

    SUPPORTED
    PARTIALLY_SUPPORTED
    DISPUTED
    NOT_ESTABLISHED
    INSUFFICIENT_EVIDENCE


## 12. Primary Source Verification

A major feature of NewsLens should be:

    News article
        |
        v
    What is the article claiming?
        |
        v
    Can we find the original source?
        |
        v
    Government document / study / court decision /
    official statistics / transcript
        |
        v
    Compare original evidence with reporting


This makes the project much stronger than simply comparing news articles.


## 13. Final Report Format

Every investigation should produce something similar to:

# Research Question

Did X cause Y?

## Executive Summary

Short neutral summary.

## Established Facts

Facts supported by reliable evidence.

## Key Claims

| Claim | Evidence | Status |
|---|---|---|
| Claim A | Source X | Supported |
| Claim B | Sources X/Y | Disputed |
| Claim C | No adequate evidence | Not established |

## Different Reporting

Explain where sources agree and where they differ.

## Primary Evidence

List relevant original documents/data.

## Important Uncertainty

Explain what cannot currently be established.

## Sources

Every major claim should link to its supporting source.


## 14. Frontend

Initial UI:

    +-----------------------------------------------+
    |                  NewsLens                     |
    +-----------------------------------------------+
    |                                               |
    | What do you want to investigate?              |
    |                                               |
    | [ Did X cause Y?________________________ ]    |
    |                                  [Research]   |
    |                                               |
    +-----------------------------------------------+


Research progress:

    Researching...

    ✓ Understanding question
    ✓ Searching news
    ✓ Reading sources
    ✓ Finding primary evidence
    → Cross-checking claims
    ○ Preparing report


Agent trace:

    14:32:08
    SEARCH
    "X Y unemployment"

    14:32:11
    FOUND
    12 sources

    14:32:14
    DECISION
    "Need official unemployment statistics."

    14:32:15
    SEARCH
    Official unemployment statistics


The trace should show actions and decisions at a high level.

Do not expose hidden chain-of-thought. Store/display concise action summaries instead.


## 15. Libraries

### Initial Python dependencies

Likely:

    fastapi
    uvicorn
    pydantic
    httpx
    python-dotenv

LLM SDK:

    provider-specific SDK

Web research:

    provider-specific search API or a search service

HTML extraction:

    beautifulsoup4
    trafilatura

Testing:

    pytest

Later:

    sqlalchemy
    psycopg
    alembic

Potentially:

    tenacity

for retries.

Do not install everything immediately.


## 16. Development Phases

### Phase 0 — Environment

Learn:

- Python virtual environments
- API keys
- environment variables
- HTTP APIs
- JSON
- basic FastAPI

Deliverable:

A Python program that can call an LLM.


### Phase 1 — Basic LLM

Build:

    user question
        ↓
    LLM
        ↓
    answer

Learn:

- messages
- system instructions
- user input
- model responses
- structured output


### Phase 2 — First Tool

Add:

    search_web()

The model can request the tool.

Build the loop manually.

Deliverable:

A basic working agent.


### Phase 3 — Multiple Steps

Allow:

    search
      ↓
    observe
      ↓
    search again
      ↓
    open page
      ↓
    answer

Add:

- maximum iteration limit
- timeout handling
- failed-tool handling


### Phase 4 — Source Handling

Create source objects.

Store:

- URL
- title
- publisher
- date
- content
- retrieval time

Deduplicate URLs.

Handle unavailable pages.


### Phase 5 — Claims & Evidence

Add structured claim extraction.

Create:

- Claim
- Evidence
- Source
- Claim status

The report becomes evidence-based rather than just a generated summary.


### Phase 6 — Primary Sources

Teach the agent to look for:

- official documents
- government statistics
- court documents
- legislation
- original research
- official statements

This becomes a major differentiating feature.


### Phase 7 — React UI

Build:

- research input
- progress indicator
- source panel
- claim table
- final report
- citations


### Phase 8 — Database

Introduce PostgreSQL.

Persist:

- research sessions
- sources
- claims
- evidence
- reports
- agent events


### Phase 9 — Evaluation

Create a fixed benchmark.

Example:

    Question 1
    Question 2
    Question 3
    ...
    Question 20

Evaluate:

- citation correctness
- source relevance
- claim extraction
- unsupported claims
- ability to identify disagreement
- ability to locate primary evidence
- tool selection
- completion rate


### Phase 10 — Production Features

Add:

- retries
- rate limiting
- caching
- logging
- observability
- error handling
- authentication
- source deduplication
- prompt/version tracking
- cost tracking
- model configuration


## 17. Safety / Quality Rules

NewsLens should follow strict research rules.

1. Never invent a source.
2. Never invent a quotation.
3. Never fabricate a URL.
4. Cite important factual claims.
5. Prefer primary sources when available.
6. Distinguish reporting from evidence.
7. Distinguish fact from interpretation.
8. Clearly identify uncertainty.
9. Do not treat political orientation as proof that a source is correct or incorrect.
10. Do not manufacture balance when evidence strongly supports one factual conclusion.
11. Do not hide meaningful disagreement between credible sources.
12. Do not let the model silently change the research question.
13. Limit agent iterations.
14. Log tool failures.
15. Verify URLs before citing them.


## 18. Agent Guardrails

The agent should have explicit boundaries.

Example:

    MAX_ITERATIONS = 10

    MAX_SEARCHES = 8

    MAX_SOURCES = 30

    MAX_PAGE_LENGTH = configured limit

If the agent cannot establish the answer:

    "Insufficient evidence to establish this claim."

It should not keep searching indefinitely.


## 19. Observability

Record events such as:

    RESEARCH_STARTED
    SEARCH_REQUESTED
    SEARCH_COMPLETED
    PAGE_OPENED
    CLAIM_EXTRACTED
    PRIMARY_SOURCE_FOUND
    DECISION_MADE
    RESEARCH_FINISHED
    TOOL_ERROR


Store:

- timestamp
- research ID
- event type
- tool
- input metadata
- result metadata
- duration
- error if any

Do not store unnecessary sensitive user data.


## 20. Testing

Create tests at multiple levels.

### Unit tests

Test:

- URL parsing
- source deduplication
- claim parsing
- state transitions
- tool validation

### Agent tests

Give the agent predefined scenarios.

Example:

    "Research claim X."

Expected:

- uses search
- opens sources
- searches for primary evidence
- produces citations


### Evaluation tests

Use a fixed dataset of research questions and compare outputs against human-reviewed expectations.

Track:

    citation_accuracy
    source_relevance
    unsupported_claim_rate
    primary_source_rate
    completion_rate
    average_iterations
    estimated_cost


## 21. Security

Important when tools can access the internet.

Implement:

- URL validation
- request timeouts
- response size limits
- domain restrictions where appropriate
- SSRF protection
- HTML sanitization
- no arbitrary local file access
- API key storage through environment variables
- rate limits

The LLM should never receive unrestricted system privileges.


## 22. Cost Control

During development:

- use inexpensive models where possible
- limit iterations
- cache search results
- cache page extraction
- avoid sending huge web pages to the LLM
- summarize/extract before passing large content forward
- log token usage

The project should track estimated research cost per query.


## 23. Git Repository Structure

Suggested structure:

    newslens/
    |
    +-- backend/
    |   +-- app/
    |       +-- api/
    |       +-- agent/
    |       +-- tools/
    |       +-- models/
    |       +-- services/
    |       +-- evaluation/
    |       +-- main.py
    |
    +-- frontend/
    |   +-- src/
    |
    +-- tests/
    |
    +-- docs/
    |
    +-- docker-compose.yml
    +-- .env.example
    +-- .gitignore
    +-- README.md


## 24. Suggested Agent Components

Eventually:

    AgentController
        ↓
    ResearchAgent
        ↓
    AgentState
        ↓
    ToolRegistry
        ├── SearchTool
        ├── OpenPageTool
        └── PrimarySourceSearchTool

    ResearchAgent
        ↓
    EvidenceAnalyzer
        ↓
    ClaimExtractor
        ↓
    ReportGenerator


Keep these components separate so the system is understandable.


## 25. Future Extensions

Once the core agent works, possible upgrades include:

### Multi-source research

Search several independent sources.

### Source diversity

Explicitly search different types of outlets and perspectives.

### Primary-source discovery

Automatically locate the underlying document behind an article.

### Fact-check mode

User supplies a claim:

    "Claim: X happened."

Agent investigates the claim.

### Debate mode

Show:

- supporting evidence
- contradicting evidence
- unresolved evidence

without forcing an artificial conclusion.

### Timeline reconstruction

Agent builds:

    Event A
       ↓
    Event B
       ↓
    Event C

with citations.

### Historical comparison

Compare current claims against historical data.

### Research memory

Remember previous investigations and sources.

### Scheduled monitoring

Monitor a topic and alert the user when significant new evidence appears.

### Browser automation

Potentially use a browser automation tool for difficult websites, subject to website policies.


## 26. What NOT to Build Initially

Avoid:

- Multi-agent systems
- Vector databases
- RAG
- Fine-tuning
- MCP
- complex memory systems
- autonomous social media posting
- autonomous email
- complicated authentication
- Kubernetes
- dozens of tools

These can come later.

The first milestone is simply:

    Question
      ↓
    Agent
      ↓
    Search
      ↓
    Observe
      ↓
    Decide
      ↓
    Search again if necessary
      ↓
    Final cited answer


## 27. First Milestone

The first version is successful when this works:

User:

    "What happened regarding X?"

Agent:

    1. Understands the question.
    2. Searches the web.
    3. Selects relevant results.
    4. Opens sources.
    5. Decides whether more research is required.
    6. Performs additional searches when necessary.
    7. Produces a concise answer.
    8. Includes source links.
    9. Clearly indicates uncertainty.


## 28. Final Portfolio Goal

The eventual résumé project should demonstrate:

- Python
- FastAPI
- React
- TypeScript
- LLM APIs
- Tool calling
- Agent orchestration
- Web research
- Structured outputs
- Evidence retrieval
- Source verification
- PostgreSQL
- Docker
- Automated evaluation
- Observability
- Error handling
- AI safety/guardrails

Potential résumé description:

"Built NewsLens, an agentic AI research system that investigates news claims through iterative web search, source analysis and primary-source verification. Implemented tool-based agent orchestration, structured claim/evidence extraction, citation tracking, uncertainty handling, evaluation benchmarks and an interactive React research dashboard."


## 29. Learning Order

Do not try to learn everything before coding.

Learn in this order:

    1. Python basics needed for the project
    2. LLM API
    3. Structured outputs
    4. Tool/function calling
    5. Agent loop
    6. Web search API
    7. Web page extraction
    8. Agent state
    9. Claims/evidence
    10. Primary-source verification
    11. FastAPI
    12. React UI
    13. PostgreSQL
    14. Docker
    15. Evaluation
    16. Observability
    17. Production hardening


## 30. Definition of Done

NewsLens is portfolio-ready when:

[ ] User can submit a research question.

[ ] Agent can independently choose research actions.

[ ] Agent can use multiple tools.

[ ] Agent can perform multiple iterations.

[ ] Agent maintains research state.

[ ] Sources are captured and deduplicated.

[ ] Important claims have evidence.

[ ] Primary sources are identified when available.

[ ] Final report contains citations.

[ ] Report distinguishes facts, claims, interpretations and uncertainty.

[ ] Agent has iteration/time/cost limits.

[ ] Tool failures are handled.

[ ] Research activity is observable.

[ ] React dashboard displays research progress.

[ ] PostgreSQL persists completed research.

[ ] Docker can run the application.

[ ] Automated evaluation dataset exists.

[ ] README explains architecture and design decisions.

[ ] At least one end-to-end demonstration is recorded.

[ ] Project can be explained clearly in a technical interview.


## 31. First Coding Session

Do NOT build the entire architecture.

First session:

    1. Create Python project.
    2. Create virtual environment.
    3. Install the LLM SDK.
    4. Store API key in .env.
    5. Make one LLM request.
    6. Understand the request/response.
    7. Add one fake tool.
    8. Let the model request the tool.
    9. Execute the tool.
    10. Send the result back to the model.
    11. Print the final answer.

The first real milestone is therefore:

    LLM
      ↓
    Tool call
      ↓
    Tool execution
      ↓
    Tool result
      ↓
    LLM
      ↓
    Answer

Once this works, we have built the core of our first agent.
