"""The bounded NewsLens research loop.

Search only discovers sources. A summary is generated solely from successfully
extracted page text, and the LLM is optional rather than a source of evidence.
"""
from datetime import datetime, timezone
from ipaddress import ip_address
from urllib.parse import urlparse
from uuid import uuid4
import json
import os
import socket

import httpx
from bs4 import BeautifulSoup
from dotenv import load_dotenv

from .models import AgentEvent, Claim, ClaimStatus, ResearchReport, Source, SourceType

load_dotenv()
MAX_SOURCES, MAX_PAGES, MAX_PAGE_BYTES, MAX_PAGE_TEXT = 8, 3, 1_500_000, 12_000
STOP_WORDS = {"about", "after", "against", "being", "could", "first", "from", "happen", "happened", "have", "into", "regarding", "their", "there", "these", "this", "what", "when", "which", "with", "would"}
UNSUITABLE_SOURCE_HOSTS = ("facebook.com", "instagram.com", "tiktok.com", "x.com", "twitter.com", "youtube.com")


def event(kind, title, detail, status="complete"):
    return AgentEvent(timestamp=datetime.now(timezone.utc), type=kind, title=title, detail=detail, status=status)


def classify(url):
    host = urlparse(url).netloc.lower()
    if any(x in host for x in ("gov", "bundestag", "europa.eu", "destatis", "who.int", "un.org")): return SourceType.PRIMARY
    if any(x in host for x in ("reuters", "apnews", "bbc", "dw.com", "nytimes", "guardian")): return SourceType.NEWS
    return SourceType.ANALYSIS


def publisher(url): return urlparse(url).netloc.removeprefix("www.") or "Unknown publisher"


def relevance_score(question, source):
    """A transparent first-pass relevance gate before any page is opened."""
    terms = {word.strip(".,?!'\"():;").lower() for word in question.split()}
    terms = {word for word in terms if len(word) > 3 and word not in STOP_WORDS}
    haystack = f"{source.title} {source.excerpt}".lower()
    return sum(term in haystack for term in terms)


def search(query):
    key = os.getenv("TAVILY_API_KEY")
    if not key: return []
    try:
        from tavily import TavilyClient
        raw = TavilyClient(api_key=key).search(query=query, max_results=MAX_SOURCES).get("results", [])
        seen, sources = set(), []
        for item in raw:
            url = item.get("url", "")
            if not url or url in seen or urlparse(url).scheme not in {"http", "https"}: continue
            seen.add(url)
            sources.append(Source(id=f"src-{len(sources)+1}", title=item.get("title", "Untitled source"), url=url, publisher=publisher(url), source_type=classify(url), excerpt=item.get("content", "")[:500]))
        return sources
    except Exception:
        return []


def is_public_url(url):
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname or parsed.username or parsed.password: return False
    try:
        addresses = {item[4][0] for item in socket.getaddrinfo(parsed.hostname, None)}
        return bool(addresses) and all(not ip_address(address).is_private and not ip_address(address).is_loopback and not ip_address(address).is_link_local for address in addresses)
    except (socket.gaierror, ValueError):
        return False


def open_page(url):
    """Fetch a public HTML document with modest network and response limits."""
    if not is_public_url(url): raise ValueError("URL is not a public HTTP(S) address")
    with httpx.Client(timeout=10, follow_redirects=False, headers={"User-Agent": "NewsLens/0.1 research prototype"}) as client:
        response = client.get(url)
        response.raise_for_status()
        if "text/html" not in response.headers.get("content-type", "").lower(): raise ValueError("Page is not HTML")
        raw = response.content[:MAX_PAGE_BYTES]
    soup = BeautifulSoup(raw, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "aside", "noscript"]): tag.decompose()
    return " ".join(soup.stripped_strings)[:MAX_PAGE_TEXT]


def fallback_summary(question, evidence):
    excerpts = []
    for source, text in evidence:
        sentence = next((part.strip() for part in text.replace("\n", " ").split(".") if len(part.strip()) > 70), "")
        if sentence: excerpts.append(f"{source.publisher} reports: {sentence}.")
    if not excerpts: return "NewsLens retrieved pages but could not extract enough readable text to summarize them."
    return "Based on the inspected sources, " + " ".join(excerpts[:2])


def llm_summary(question, evidence):
    """Ask local Ollama for an evidence-constrained JSON report, if available."""
    model = os.getenv("OLLAMA_MODEL", "gemma3:4b")
    material = "\n\n".join(f"[{source.id}] {source.title}\n{text[:3500]}" for source, text in evidence)
    prompt = f'''Question: {question}
Sources (only these may be cited):\n{material}

Return valid JSON with keys summary (2-4 neutral sentences that directly answer the question first), facts (array of up to 3 statements), claim (one careful statement that directly answers the question), evidence (why the material supports or limits it), status (SUPPORTED, PARTIALLY_SUPPORTED, DISPUTED, NOT_ESTABLISHED, or INSUFFICIENT_EVIDENCE), source_ids (array). Do not invent facts, quotes, URLs, or source IDs. If the sources do not document the requested reaction, say it is not established. State uncertainty where needed.'''
    try:
        from ollama import chat
        result = chat(model=model, messages=[{"role": "user", "content": prompt}], format="json")
        data = json.loads(result.message.content)
        valid_ids = {source.id for source, _ in evidence}
        data["source_ids"] = [i for i in data.get("source_ids", []) if i in valid_ids]
        if not data["source_ids"]: return None
        ClaimStatus(data["status"])
        return data
    except Exception:
        return None


def investigate(question):
    events = [event("RESEARCH_STARTED", "Research question received", "Preserving the question exactly as submitted."), event("DECISION_MADE", "Scoped the investigation", "Seeking reporting and primary evidence.")]
    sources = search(question)
    if not sources:
        source = Source(id="demo-1", title="Demo research requires a configured search provider", url="https://www.tavily.com/", publisher="NewsLens demo", source_type=SourceType.OFFICIAL)
        events += [event("TOOL_ERROR", "Live search unavailable", "No usable Tavily response was available; no live sources were invented.", "warning"), event("RESEARCH_FINISHED", "Prepared a safe preliminary report", "Add TAVILY_API_KEY to enable live discovery.")]
        return ResearchReport(id=str(uuid4()), question=question, executive_summary="The agent could not retrieve live sources, so it cannot responsibly summarize this question.", established_facts=["No live research result was used."], claims=[Claim(statement="The question can be answered from the current evidence.", evidence="No live sources were retrieved.", status=ClaimStatus.INSUFFICIENT_EVIDENCE)], uncertainty="Configure a search provider and rerun this investigation.", sources=[source], events=events, iterations=1, mode="safe-demo")
    events += [event("SEARCH_REQUESTED", "Searching the web", question), event("SEARCH_COMPLETED", "Collected candidate sources", f"Retained {len(sources)} unique URLs after deduplication.")]
    eligible = [source for source in sources if not any(host in urlparse(source.url).netloc.lower() for host in UNSUITABLE_SOURCE_HOSTS)]
    ranked = sorted(eligible, key=lambda source: (relevance_score(question, source), source.source_type in {SourceType.PRIMARY, SourceType.NEWS}), reverse=True)
    selected = [source for source in ranked if relevance_score(question, source) > 0][:MAX_PAGES]
    if not selected:
        events.append(event("DECISION_MADE", "Stopped before reading unrelated pages", "None of the returned results passed the transparent relevance check.", "warning"))
        return ResearchReport(id=str(uuid4()), question=question, executive_summary="Search returned material, but none was relevant enough to inspect safely for this question.", established_facts=["No search result passed NewsLens's first-pass relevance check."], claims=[Claim(statement="The returned sources answer the question.", evidence="The title and search excerpt did not match the investigation terms.", status=ClaimStatus.INSUFFICIENT_EVIDENCE)], uncertainty="Try a more specific question or refine the search query.", sources=sources, events=events, iterations=2, mode="live-relevance-failed")
    events.append(event("DECISION_MADE", "Selected relevant sources", f"Opening {len(selected)} source(s) after relevance screening."))
    evidence = []
    for source in selected:
        try:
            events.append(event("PAGE_OPENED", "Reading source", source.publisher))
            text = open_page(source.url)
            if len(text) < 250: raise ValueError("Too little readable text")
            evidence.append((source, text))
        except Exception as exc:
            events.append(event("TOOL_ERROR", "Could not read source", f"{source.publisher}: {str(exc)[:90]}", "warning"))
    if not evidence:
        return ResearchReport(id=str(uuid4()), question=question, executive_summary="Relevant sources were found, but no page could be safely read and verified. NewsLens will not summarize uninspected snippets.", established_facts=["Search results were found but not used as verified evidence."], claims=[Claim(statement="The available search snippets establish the answer.", evidence="No source page was successfully extracted.", status=ClaimStatus.INSUFFICIENT_EVIDENCE)], uncertainty="Try again later or use sources that permit ordinary HTML access.", sources=sources, events=events, iterations=2, mode="live-retrieval-failed")
    generated = llm_summary(question, evidence)
    if generated:
        summary, facts = generated["summary"], generated.get("facts", [])
        claim = Claim(statement=generated.get("claim", "The inspected evidence supports a cautious conclusion."), evidence=generated.get("evidence", "See cited source text."), status=ClaimStatus(generated["status"]), source_ids=generated["source_ids"])
        mode = "live-llm-summary"
        events.append(event("CLAIM_EXTRACTED", "Synthesized inspected evidence", f"Used {len(generated['source_ids'])} cited sources."))
    else:
        summary, facts = fallback_summary(question, evidence), [f"NewsLens inspected {len(evidence)} source page(s) before producing this preliminary summary."]
        claim = Claim(statement="The inspected pages contain relevant reporting on the question.", evidence="This is a preliminary extraction, not a final fact-check.", status=ClaimStatus.PARTIALLY_SUPPORTED, source_ids=[source.id for source, _ in evidence])
        mode = "live-extractive-summary"
        events.append(event("CLAIM_EXTRACTED", "Prepared extractive summary", "Local synthesis was unavailable; this is not a direct answer to nuanced questions.", "warning"))
    events.append(event("RESEARCH_FINISHED", "Research report prepared", "Every summary path is tied to inspected source content."))
    return ResearchReport(id=str(uuid4()), question=question, executive_summary=summary, established_facts=facts[:3], claims=[claim], uncertainty="This is a bounded first-pass investigation. Check the cited sources and seek primary evidence for consequential claims.", sources=sources, events=events, iterations=2, mode=mode)
