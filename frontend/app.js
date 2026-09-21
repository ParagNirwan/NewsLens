const form = document.querySelector('#research-form'),
  question = document.querySelector('#question'),
  result = document.querySelector('#result');

const esc = s =>
  String(s).replace(
    /[&<>'"]/g,
    c =>
      ({
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        "'": '&#39;',
        '"': '&quot;'
      }[c])
  );

const PHASES = [
  'Defining scope, selecting sources, and preserving uncertainty…',
  'Searching news coverage and official records…',
  'Screening candidate sources for relevance and domain integrity…',
  'Inspecting and extracting readable source documents…',
  'Cross-checking evidence and synthesizing findings…'
];

let phaseInterval = null;

form.addEventListener('submit', async e => {
  e.preventDefault();
  const b = form.querySelector('button');
  b.disabled = true;
  b.innerHTML = 'Investigating <span class="dot-flashing"><span>.</span><span>.</span><span>.</span></span>';
  result.className = 'result';

  let phaseIndex = 0;
  result.innerHTML = `
    <div class="loading">
      <div class="loading-header">
        <span class="agent-beacon" aria-hidden="true"></span>
        <b>AGENT ACTIVE</b>
      </div>
      <div class="loading-scan" aria-hidden="true"></div>
      <div class="loading-ticker">
        <span id="loading-stage">${esc(PHASES[0])}</span>
      </div>
      <div class="loading-skeleton" aria-hidden="true">
        <div class="skeleton-line w-80"></div>
        <div class="skeleton-line w-60"></div>
        <div class="skeleton-row">
          <div class="skeleton-card">
            <div class="skeleton-line w-40"></div>
            <div class="skeleton-line w-80"></div>
          </div>
          <div class="skeleton-card">
            <div class="skeleton-line w-60"></div>
            <div class="skeleton-line w-40"></div>
          </div>
        </div>
      </div>
    </div>
  `;

  if (phaseInterval) clearInterval(phaseInterval);
  phaseInterval = setInterval(() => {
    phaseIndex = (phaseIndex + 1) % PHASES.length;
    const stageEl = document.querySelector('#loading-stage');
    if (stageEl) {
      stageEl.style.animation = 'none';
      void stageEl.offsetHeight; // trigger reflow to replay fade animation
      stageEl.style.animation = '';
      stageEl.textContent = PHASES[phaseIndex];
    }
  }, 2600);

  try {
    const res = await fetch('/api/research', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question: question.value })
    });
    if (!res.ok) throw Error('Research request failed');
    render(await res.json());
  } catch (err) {
    result.innerHTML = `<div class="error"><b>Research paused</b><p>${esc(err.message)}. Please try again.</p></div>`;
  } finally {
    if (phaseInterval) {
      clearInterval(phaseInterval);
      phaseInterval = null;
    }
    b.disabled = false;
    b.innerHTML = 'Research <span>↗</span>';
  }
});

function render(r) {
  const ev = r.events
    .map(
      e =>
        `<li class="${e.status}"><time>${new Date(
          e.timestamp
        ).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</time><b>${esc(
          e.title
        )}</b><small>${esc(e.detail)}</small></li>`
    )
    .join('');

  const cl = r.claims
    .map(
      c =>
        `<article class="claim"><span class="pill ${c.status.toLowerCase()}">${esc(
          c.status.replaceAll('_', ' ')
        )}</span><h3>${esc(c.statement)}</h3><p>${esc(c.evidence)}</p></article>`
    )
    .join('');

  const src = r.sources
    .map(
      s =>
        `<a class="source" href="${esc(s.url)}" target="_blank" rel="noreferrer"><span>${esc(
          s.source_type
        )}</span><b>${esc(s.title)}</b><small>${esc(s.publisher)} ↗</small></a>`
    )
    .join('');

  result.innerHTML = `
    <div class="report-head">
      <p class="eyebrow">${esc(r.mode)} / ${r.iterations} iteration</p>
      <h2>${esc(r.question)}</h2>
      <p>${esc(r.executive_summary)}</p>
    </div>
    <div class="research-grid">
      <section>
        <h4>Research trace</h4>
        <ol class="trace">${ev}</ol>
      </section>
      <section>
        <h4>Key claims</h4>
        ${cl}
      </section>
    </div>
    <section class="facts">
      <h4>Established facts</h4>
      <ul>${r.established_facts.map(x => `<li>${esc(x)}</li>`).join('')}</ul>
      <p><b>Important uncertainty:</b> ${esc(r.uncertainty)}</p>
    </section>
    <section class="sources">
      <h4>Source record</h4>
      ${src}
    </section>
  `;
}
