const $ = id => document.getElementById(id);
const escapeHTML = value => String(value ?? '').replace(/[&<>"']/g, ch => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch]));
const state = {concepts:[], records:[], studio:null, metrics:null, scenario:null, step:0, concept:'process', studioTab:'knowledge', studioSource:0, studioCase:0, scheduleResult:null, scheduleStep:0};

async function json(url, options) {
  const response = await fetch(url, options);
  const data = await response.json();
  if (!response.ok) throw Error(data.error || `HTTP ${response.status}`);
  return data;
}

function navigate(page) {
  const valid = ['home','learn','explore','schedule','practice','debug','studio'];
  if (!valid.includes(page)) page = 'home';
  document.querySelectorAll('.page').forEach(item => item.classList.toggle('active', item.id === `page-${page}`));
  document.querySelectorAll('.nav-item').forEach(item => item.classList.toggle('active', item.dataset.page === page));
  $('breadcrumb').textContent = `${page.toUpperCase()} / ${page === 'home' ? 'START HERE' : page === 'explore' ? 'FORK & WAIT' : 'OSLAB COPILOT'}`;
  if (location.hash !== `#${page}` && !location.hash.startsWith(`#${page}?`)) history.replaceState(null,'',`#${page}`);
  if (page === 'explore' && state.scenario) renderScenario();
  if (page === 'practice') renderPractice();
  if (page === 'studio' && state.studio) renderStudio();
  if (page === 'schedule' && state.scheduleResult) renderSchedule();
  window.scrollTo(0,0);
}

function renderConcepts() {
  $('concept-list').innerHTML = state.concepts.map(item => `<button class="concept-item ${item.id === state.concept ? 'active' : ''}" data-concept="${escapeHTML(item.id)}"><strong>${escapeHTML(item.title)}</strong><small>${escapeHTML(item.prerequisites.length ? `After ${item.prerequisites.join(', ')}` : 'Start here')}</small></button>`).join('');
  const item = state.concepts.find(c => c.id === state.concept) || state.concepts[0];
  if (!item) return;
  const linked = item.source_records.map(id => state.records.find(record => record.id === id)).filter(Boolean);
  $('concept-detail').innerHTML = `<div class="concept-detail"><span class="tag">${escapeHTML(item.area)}</span><h2 style="margin-top:15px">${escapeHTML(item.title)}</h2><p>${escapeHTML(item.summary)}</p><div class="eyebrow">WHAT TO REMEMBER</div><ul>${item.claims.map(x => `<li>${escapeHTML(x)}</li>`).join('')}</ul><div class="eyebrow">COMMON MISCONCEPTIONS</div><ul>${item.misconceptions.map(x => `<li>${escapeHTML(x.text)}</li>`).join('')}</ul>${linked.length ? `<div class="eyebrow">CONNECTED EVIDENCE</div>${linked.map(r => `<div class="record-item"><strong>${escapeHTML(r.experiment_id)} · ${escapeHTML(r.section_type)}</strong><small>${escapeHTML(r.text)}</small></div>`).join('')}` : '<p class="caption">Original concept record; lab retrieval records have not yet been mapped to this topic.</p>'}<div class="eyebrow">READ FURTHER</div><div class="source-links">${item.references.map(ref => `<a href="${escapeHTML(ref.url)}" target="_blank" rel="noopener noreferrer">${escapeHTML(ref.title)} ↗</a>`).join('')}</div><p><button class="primary small" data-go="${item.simulator === 'schedule' ? 'schedule' : 'explore'}">Open ${item.simulator === 'schedule' ? 'scheduling lab' : 'process model'} →</button></p></div>`;
}

async function loadScenario() {
  const useWait = $('use-wait').checked;
  const schedule = $('schedule').value;
  state.scenario = await json(`/api/process?wait=${useWait ? 1 : 0}&schedule=${schedule}`);
  state.step = 0;
  $('compare-result').innerHTML = '';
  renderScenario();
  renderPractice();
}

function renderScenario() {
  const scenario = state.scenario;
  if (!scenario) return;
  const frame = scenario.frames[state.step], model = frame.state;
  $('model-code').innerHTML = scenario.code.map((line,index) => `<div class="code-line ${frame.code_line === index ? 'active' : ''}"><span class="line-number">${String(index+1).padStart(2,'0')}</span><span>${escapeHTML(line)}</span></div>`).join('');
  $('step-count').textContent = `STEP ${state.step} / ${scenario.frames.length-1}`;
  $('frame-title').textContent = frame.title;
  $('parent-node').className = `process-node ${model.parent === 'BLOCKED' ? 'blocked' : model.parent === 'EXITED' ? 'exited' : ''}`;
  $('child-node').className = `process-node ${model.child === 'NOT_CREATED' ? 'absent' : model.child === 'EXITED' ? 'exited' : ''}`;
  $('parent-node').querySelector('strong').textContent = model.parent;
  $('child-node').querySelector('strong').textContent = model.child;
  $('state-detail').innerHTML = `<b>Active:</b> ${escapeHTML(model.active || 'none')}<br><b>Child reaped:</b> ${model.child_reaped ? 'yes' : 'no'}<br><b>Model output:</b> ${escapeHTML(model.output.join(' → ') || 'none yet')}`;
  $('step-back').disabled = state.step === 0;
  $('step-next').disabled = state.step === scenario.frames.length-1;
  $('timeline').innerHTML = scenario.frames.map((f,index) => `<button class="${index === state.step ? 'active' : ''}" data-step="${index}"><b>${String(index).padStart(2,'0')} · ${escapeHTML(f.event)}</b><span>${escapeHTML(f.title)}</span></button>`).join('');
}

async function compareRuns() {
  const [withWait,parentFirst,childFirst] = await Promise.all([
    json('/api/process?wait=1&schedule=parent_first'),
    json('/api/process?wait=0&schedule=parent_first'),
    json('/api/process?wait=0&schedule=child_first')
  ]);
  const card = (title,data) => `<div class="compare-card"><strong>${escapeHTML(title)}</strong><ol>${data.frames.at(-1).state.output.map(x => `<li>${escapeHTML(x)}</li>`).join('')}</ol></div>`;
  $('compare-result').innerHTML = card('With wait: child completes first',withWait) + card('No wait: parent may finish first',parentFirst) + card('No wait: child may finish first',childFirst);
}

function renderPractice() {
  if (!state.scenario) return;
  const useWait = $('use-wait').checked;
  const schedule = $('schedule').value;
  $('practice-mode').textContent = `${useWait ? 'WITH WAIT' : 'NO WAIT'} · ${schedule.replace('_',' ').toUpperCase()}`;
  $('practice-context').innerHTML = `The <code>fork()</code> call just returned. The parent is running and the child is ready. ${useWait ? 'The parent code includes waitpid().' : 'The parent code has no waitpid().'} Which event comes next in the selected model schedule?`;
  const choices = [['PARENT_WAIT','Parent blocks in waitpid'],['CHILD_RUN','Child is selected to run'],['PARENT_OUTPUT','Parent prints completion']];
  $('practice-options').innerHTML = choices.map(([value,label]) => `<button data-answer="${value}">${escapeHTML(label)}</button>`).join('');
  $('practice-feedback').textContent = '';
  $('practice-feedback').className = 'feedback';
}

async function answerPractice(answer) {
  try {
    const data = await json('/api/practice',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({use_wait:$('use-wait').checked,schedule:$('schedule').value,step:1,answer})});
    $('practice-feedback').className = `feedback ${data.correct ? '' : 'wrong'}`;
    $('practice-feedback').innerHTML = `<strong>${data.correct ? 'Correct.' : 'Not in this selected schedule.'}</strong> ${escapeHTML(data.explanation)}${data.misconception_id ? `<br><small>Misconception signal: ${escapeHTML(data.misconception_id)}</small>` : ''}`;
  } catch(error) { $('practice-feedback').textContent = error.message; }
}

async function analyse() {
  $('result').innerHTML = '<p>Analysing evidence…</p>';
  try {
    const data = await json('/api/analyse',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({experiment:$('experiment').value,mode:$('mode').value,question:$('question').value,code:$('code').value,output:$('output').value})});
    let html = `<span class="tag">${escapeHTML(data.evidence_strength || data.execution_status)}</span><h2 style="margin-top:15px">${escapeHTML(data.likely_issue || 'Instructional evidence')}</h2>`;
    if (data.supporting_signals?.length) html += `<h3>Evidence</h3><ul>${data.supporting_signals.map(x => `<li>${escapeHTML(x)}</li>`).join('')}</ul>`;
    if (data.expected_behaviour?.length) html += `<h3>Expected vs inferred</h3><p><b>Expected:</b> ${escapeHTML(data.expected_behaviour.join(' → '))}</p><p><b>From source or pasted output:</b> ${escapeHTML(data.observed_behaviour.join(' → ') || 'No evidence supplied')}</p>`;
    if (data.matched_failure_cases?.length) html += `<h3>Similar cases</h3><ul>${data.matched_failure_cases.map(x => `<li><b>${escapeHTML(x.id)}</b> · ${escapeHTML(x.failure_label)} · matching: ${escapeHTML(x.matched_signals.join(', '))}</li>`).join('')}</ul>`;
    html += `<h3>Retrieved evidence</h3>${data.retrieved_sources.map(r => `<div class="source-row"><b>${escapeHTML(r.experiment_id)} · ${escapeHTML(r.section_type)}</b><p>${escapeHTML(r.text)}</p><small>${escapeHTML(r.source)} · lexical ${escapeHTML(r.lexical_score)} · LSA ${escapeHTML(r.semantic_score)} · fused ${escapeHTML(r.fused_score)}</small></div>`).join('')}`;
    html += `<h3>Explanation</h3><p>${escapeHTML(data.explanation)}</p>`;
    if (data.next_check) html += `<p><b>Next check:</b> ${escapeHTML(data.next_check)}</p>`;
    if (data.visual_lesson) html += `<button class="primary small" id="open-lesson">Open visual explanation →</button>`;
    html += `<details><summary>Technical view · complete structured result</summary><pre>${escapeHTML(JSON.stringify(data,null,2))}</pre></details>`;
    $('result').innerHTML = html;
    if (data.visual_lesson) $('open-lesson').onclick = async () => { $('use-wait').checked = !data.visual_lesson.endsWith('wait=0'); await loadScenario(); navigate('explore'); };
  } catch(error) { $('result').innerHTML = `<h2>Analysis failed</h2><p>${escapeHTML(error.message)}</p>`; }
}

function addProcess(id='',arrival=0,burst=2) {
  const row = document.createElement('div');
  row.className = 'workload-row';
  row.innerHTML = `<label>ID<input class="pid" maxlength="8" value="${escapeHTML(id)}"></label><label>Arrival<input class="arrival" type="number" min="0" max="20" value="${arrival}"></label><label>Burst<input class="burst" type="number" min="1" max="20" value="${burst}"></label><button class="remove-process" title="Remove process" aria-label="Remove process">×</button>`;
  row.querySelector('button').onclick = () => row.remove();
  $('workload-rows').append(row);
}

async function runSchedule() {
  const processes = [...document.querySelectorAll('.workload-row')].map(row => ({id:row.querySelector('.pid').value.trim(),arrival:Number(row.querySelector('.arrival').value),burst:Number(row.querySelector('.burst').value)}));
  try {
    state.scheduleResult = await json('/api/schedule',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({processes,algorithm:$('schedule-algorithm').value,quantum:Number($('schedule-quantum').value)})});
    state.scheduleStep = 0;
    renderSchedule();
  } catch(error) { $('schedule-state').innerHTML = `<div class="warning">${escapeHTML(error.message)}</div>`; }
}

function renderSchedule() {
  const result = state.scheduleResult;
  if (!result) return;
  const frame = result.frames[state.scheduleStep], snapshot = frame.state;
  $('schedule-step').textContent = `EVENT ${state.scheduleStep} / ${result.frames.length-1} · t=${frame.time}`;
  $('schedule-state').innerHTML = `<h2>${escapeHTML(frame.title)}</h2><div class="record-grid"><div class="record-item"><strong>Running</strong><small>${escapeHTML(snapshot.running || 'none')}</small></div><div class="record-item"><strong>Ready queue</strong><small>${escapeHTML(snapshot.ready.join(' → ') || 'empty')}</small></div></div><table class="metric-table"><thead><tr><th>Process</th><th>Status</th><th>Remaining</th></tr></thead><tbody>${Object.values(snapshot.processes).map(item => `<tr><td>${escapeHTML(item.id)}</td><td>${escapeHTML(item.status)}</td><td>${item.remaining}</td></tr>`).join('')}</tbody></table>`;
  $('schedule-back').disabled = state.scheduleStep === 0;
  $('schedule-next').disabled = state.scheduleStep === result.frames.length-1;
  $('gantt').innerHTML = result.gantt.filter(slot => slot.time < frame.time).map(slot => `<div class="gantt-cell done"><strong>${escapeHTML(slot.process)}</strong><small>${slot.time}–${slot.time+1}</small></div>`).join('') || '<p class="caption">Step through events to reveal the CPU timeline.</p>';
  $('schedule-metrics').innerHTML = state.scheduleStep === result.frames.length-1 ? `<h2 style="margin-top:23px">Calculated metrics</h2><table class="metric-table"><thead><tr><th>Process</th><th>Waiting</th><th>Turnaround</th><th>Response</th></tr></thead><tbody>${Object.entries(result.metrics).map(([pid,m]) => `<tr><td>${escapeHTML(pid)}</td><td>${m.waiting}</td><td>${m.turnaround}</td><td>${m.response}</td></tr>`).join('')}</tbody></table><p class="caption">${escapeHTML(result.tie_break)} CPU-only workload; no I/O blocking or context-switch cost.</p>` : '';
}

function renderStudio() {
  const audit = state.studio;
  if (!audit) return;
  const kh = audit.knowledge.health, bh = audit.behaviour.health;
  $('dataset-version').textContent = `DATASET ${audit.dataset_version}`;
  $('studio-summary').innerHTML = [[kh.source_count,'raw sources'],[kh.record_count,'instructional records'],[bh.case_count,'behaviour cases'],[bh.observed_trace_count,'runtime traces']].map(([number,label]) => `<div class="stat"><strong>${number}</strong><small>${label}</small></div>`).join('');
  $('pipeline').innerHTML = audit.pipeline.map(x => `<span>${escapeHTML(x)}</span>`).join('');
  document.querySelectorAll('[data-studio]').forEach(x => x.classList.toggle('active',x.dataset.studio === state.studioTab));
  if (state.studioTab === 'knowledge') renderStudioKnowledge();
  else if (state.studioTab === 'behaviour') renderStudioBehaviour();
  else renderStudioEvaluation();
}

function renderStudioKnowledge() {
  const audit = state.studio.knowledge;
  const source = audit.sources[state.studioSource];
  const records = audit.records.filter(r => r.source === source.source);
  $('studio-content').innerHTML = `<div class="studio-layout"><div class="studio-list">${audit.sources.map((s,index) => `<button class="${index === state.studioSource ? 'active' : ''}" data-source="${index}"><strong>${escapeHTML(s.source)}</strong><br><small>${s.record_count} records · ${s.sections.length} sections</small></button>`).join('')}</div><div class="studio-detail"><h2>${escapeHTML(source.source)}</h2><div class="meta">${escapeHTML(source.path)} · SHA-256 ${escapeHTML(source.source_sha256)}</div><p>${escapeHTML(source.extraction)}. ${source.sections.length} logical sections were detected.</p><div class="record-grid">${source.sections.map(s => `<div class="record-item"><strong>${escapeHTML(s.name)}</strong><small>line ${s.line} · ${s.record_ids.length} record</small></div>`).join('')}</div><details><summary>1 · Raw source document</summary><pre>${escapeHTML(source.raw_text)}</pre></details><details open><summary>2 · Processed records and metadata</summary>${records.map(r => `<div class="record-item" style="margin-top:9px"><strong>${escapeHTML(r.id)} · ${escapeHTML(r.section_type)}</strong><small>${escapeHTML(r.text)}</small><div class="meta" style="margin-top:7px">topic: ${escapeHTML(r.topic)} · language: ${escapeHTML(r.language)} · hash: ${escapeHTML(r.content_hash.slice(0,16))}…</div></div>`).join('')}</details><p class="caption">Health: ${audit.health.missing_metadata_count} missing metadata fields; ${audit.health.duplicate_count_after_filter} duplicates after filtering; ${audit.health.warnings.length} warnings.</p></div></div>`;
}

function renderStudioBehaviour() {
  const corpus = state.studio.behaviour, item = corpus.cases[state.studioCase];
  $('studio-content').innerHTML = `<div class="studio-layout"><div class="studio-list">${corpus.cases.map((c,index) => `<button class="${index === state.studioCase ? 'active' : ''}" data-case="${index}"><strong>${escapeHTML(c.id)}</strong><br><small>${escapeHTML(c.label)} · ${escapeHTML(c.evidence_level)}</small></button>`).join('')}</div><div class="studio-detail"><h2>${escapeHTML(item.id)}</h2><div class="meta">${escapeHTML(item.source_path)} · SHA-256 ${escapeHTML(item.source_sha256)}</div><p><b>Controlled change:</b> ${escapeHTML(item.mutation_description)}</p><div class="record-grid"><div class="record-item"><strong>Expected</strong><small>${escapeHTML(item.expected_events.join(' → '))}</small></div><div class="record-item"><strong>Inferred from source</strong><small>${escapeHTML(item.inferred_from_source.join(', '))}</small></div><div class="record-item"><strong>Observed at runtime</strong><small>${item.observed_at_runtime.length ? escapeHTML(item.observed_at_runtime.join(', ')) : 'None collected'}</small></div></div><div class="warning">${escapeHTML(item.runtime_status)}. No runtime trace is claimed for this case.</div><details open><summary>1 · Reviewed C source</summary><pre>${escapeHTML(item.source_code)}</pre></details>${item.source_diff ? `<details><summary>2 · Source difference from reference</summary><pre>${escapeHTML(item.source_diff)}</pre></details>` : ''}<details><summary>3 · Extracted static features</summary><pre>${escapeHTML(JSON.stringify(item.features,null,2))}</pre></details></div></div>`;
}

function renderStudioEvaluation() {
  const metrics = state.metrics;
  if (!metrics) { $('studio-content').textContent = 'Evaluation metrics unavailable.'; return; }
  const methods = metrics.retrieval.methods;
  const pm = metrics.processing;
  $('studio-content').innerHTML = `<h2>Processing quality</h2><p>${pm.labelled_section_count} labelled headings in ${pm.source_count} synthetic Markdown sources. Heading precision ${pm.section_heading_precision.toFixed(3)}, recall ${pm.section_heading_recall.toFixed(3)}; experiment ID accuracy ${pm.experiment_id_accuracy.toFixed(3)}; metadata completeness ${pm.metadata_completeness.toFixed(3)}. ${escapeHTML(pm.qualification)}</p><h2 style="margin-top:28px">Measured retrieval benchmark</h2><p>${metrics.retrieval.query_count} labelled queries over synthetic demo records. These results are a regression baseline, not open-ended OS teaching performance.</p><table class="metric-table"><thead><tr><th>Method</th><th>Recall@3</th><th>MRR@10</th><th>nDCG@10</th></tr></thead><tbody>${Object.entries(methods).map(([name,m]) => `<tr><td>${escapeHTML(name)}</td><td>${m.recall_at_3.toFixed(3)}</td><td>${m.mrr_at_10.toFixed(3)}</td><td>${m.ndcg_at_10.toFixed(3)}</td></tr>`).join('')}</tbody></table><h2 style="margin-top:28px">Failure matching</h2><p>Top-1: ${Math.round(metrics.diagnostic.top1_accuracy*metrics.diagnostic.case_count)}/${metrics.diagnostic.case_count}; Top-3: ${Math.round(metrics.diagnostic.top3_accuracy*metrics.diagnostic.case_count)}/${metrics.diagnostic.case_count}. ${escapeHTML(metrics.diagnostic.evidence)}</p><details><summary>Per-case predictions</summary><pre>${escapeHTML(JSON.stringify(metrics.diagnostic.cases,null,2))}</pre></details>`;
}

document.addEventListener('click', async event => {
  const go = event.target.closest('[data-go]'); if (go) { navigate(go.dataset.go); return; }
  const nav = event.target.closest('[data-page]'); if (nav) { navigate(nav.dataset.page); return; }
  const concept = event.target.closest('[data-concept]'); if (concept) { state.concept = concept.dataset.concept; renderConcepts(); return; }
  const step = event.target.closest('[data-step]'); if (step) { state.step = Number(step.dataset.step); renderScenario(); return; }
  const answer = event.target.closest('[data-answer]'); if (answer) { await answerPractice(answer.dataset.answer); return; }
  const tab = event.target.closest('[data-studio]'); if (tab) { state.studioTab = tab.dataset.studio; renderStudio(); return; }
  const source = event.target.closest('[data-source]'); if (source) { state.studioSource = Number(source.dataset.source); renderStudioKnowledge(); return; }
  const caseButton = event.target.closest('[data-case]'); if (caseButton) { state.studioCase = Number(caseButton.dataset.case); renderStudioBehaviour(); }
});

window.addEventListener('hashchange', () => { const [page,query] = location.hash.slice(1).split('?'); if (page === 'explore' && query?.includes('wait=0')) { $('use-wait').checked = false; loadScenario(); } navigate(page); });
$('use-wait').onchange = loadScenario;
$('schedule').onchange = loadScenario;
$('step-back').onclick = () => { if (state.step > 0) { state.step--; renderScenario(); } };
$('step-next').onclick = () => { if (state.scenario && state.step < state.scenario.frames.length-1) { state.step++; renderScenario(); } };
$('compare').onclick = compareRuns;
$('practice-switch').onclick = async () => { $('use-wait').checked = !$('use-wait').checked; await loadScenario(); };
$('analyse').onclick = analyse;
$('add-process').onclick = () => addProcess(`P${document.querySelectorAll('.workload-row').length+1}`,0,2);
$('run-schedule').onclick = runSchedule;
$('schedule-back').onclick = () => { if (state.scheduleStep > 0) { state.scheduleStep--; renderSchedule(); } };
$('schedule-next').onclick = () => { if (state.scheduleResult && state.scheduleStep < state.scheduleResult.frames.length-1) { state.scheduleStep++; renderSchedule(); } };
$('schedule-final').onclick = () => { if (state.scheduleResult) { state.scheduleStep = state.scheduleResult.frames.length-1; renderSchedule(); } };
$('load-demo').onclick = () => { $('experiment').value='FW01'; $('mode').value='Debug'; $('question').value='Why can the parent finish before the child?'; $('code').value=state.studio?.behaviour.cases.find(c=>c.id==='missing_wait_a')?.source_code || ''; $('output').value=''; };

(async function init(){
  try {
    [state.concepts,state.records,state.studio,state.metrics] = await Promise.all([json('/api/concepts'),json('/api/records'),json('/api/studio'),json('/api/metrics')]);
    renderConcepts();
    addProcess('P1',0,5); addProcess('P2',1,3); addProcess('P3',2,1);
    const [page,query] = location.hash.slice(1).split('?');
    if (page === 'explore' && query?.includes('wait=0')) $('use-wait').checked = false;
    await loadScenario();
    navigate(page || 'home');
  } catch(error) { document.querySelector('main').insertAdjacentHTML('afterbegin',`<div class="warning">Could not load local data: ${escapeHTML(error.message)}</div>`); }
})();
