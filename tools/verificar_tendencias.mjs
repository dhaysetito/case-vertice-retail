// Verificacao headless da secao "Evolucao e tendencias". Roda em Linux, ao
// contrario de verificar_prototipo.mjs, que fixa o caminho do Edge no Windows.
//
// Pre-requisitos, nesta ordem:
//   1. python3 -m app.server
//   2. python3 -m http.server 8000 --directory docs/prototipo
//   3. node tools/verificar_tendencias.mjs
//
// Protege as correcoes de 2026-09-20 (docs/18-correcoes-tendencias.md):
//   - a tabela de valores segue a granularidade, em vez de dizer "mensais" sempre
//   - a semana 53 nao desenha dias fora da cobertura da base
//   - trocar de granularidade mantem o periodo em que o usuario estava
//   - as frentes de negocio sao selecionaveis tambem nesta secao
import {spawn} from 'node:child_process';
import assert from 'node:assert/strict';

const ALVO = process.env.DASHBOARD_URL || 'http://127.0.0.1:8000/index.html';
const PORTA_CDP = 9400;

const browser = spawn('google-chrome', [
  '--headless=new', '--disable-gpu', '--no-sandbox', '--no-first-run', '--no-default-browser-check',
  `--remote-debugging-port=${PORTA_CDP}`, '--user-data-dir=/tmp/chrome-verificar-tendencias', 'about:blank',
], {stdio: 'ignore'});

let ws, falhou = 0;
const log = (ok, texto) => {console.log(`${ok ? '  OK  ' : ' FALHA'} ${texto}`); if (!ok) falhou++;};

try {
  let tabs;
  for (let i = 0; i < 60; i++) {
    try {tabs = await (await fetch(`http://127.0.0.1:${PORTA_CDP}/json`)).json(); if (tabs.some(t => t.type === 'page')) break;} catch {}
    await new Promise(r => setTimeout(r, 250));
  }
  assert(tabs, 'Chrome nao abriu a porta de depuracao');
  ws = new WebSocket(tabs.find(t => t.type === 'page').webSocketDebuggerUrl);
  await new Promise((res, rej) => {ws.onopen = res; ws.onerror = rej;});

  let id = 0; const pendentes = new Map(); const excecoes = [];
  ws.onmessage = e => {
    const m = JSON.parse(e.data);
    if (m.id) {const p = pendentes.get(m.id); pendentes.delete(m.id); m.error ? p.reject(m.error) : p.resolve(m.result);}
    if (m.method === 'Runtime.exceptionThrown') excecoes.push(m.params.exceptionDetails.text);
  };
  const send = (metodo, params = {}) => new Promise((resolve, reject) => {
    const n = ++id; pendentes.set(n, {resolve, reject}); ws.send(JSON.stringify({id: n, method: metodo, params}));
  });
  const ev = async expressao => {
    const r = await send('Runtime.evaluate', {expression: expressao, returnByValue: true, awaitPromise: true});
    assert(!r.exceptionDetails, JSON.stringify(r.exceptionDetails));
    return r.result.value;
  };
  const filtrar = async (campo, valor) => {
    await ev(`(()=>{const s=document.getElementById('${campo}');s.value=${JSON.stringify(valor)};s.dispatchEvent(new Event('change',{bubbles:true}));})()`);
    await new Promise(r => setTimeout(r, 800));
  };

  await send('Runtime.enable'); await send('Page.enable');
  await send('Emulation.setDeviceMetricsOverride', {width: 1440, height: 1050, deviceScaleFactor: 1, mobile: false});
  await send('Page.navigate', {url: `${ALVO}#tendencias`});
  for (let i = 0; i < 40; i++) {if (await ev("document.body.dataset.section==='tendencias'")) break; await new Promise(r => setTimeout(r, 300));}
  await new Promise(r => setTimeout(r, 1200));

  // 1. a tabela de valores acompanha a granularidade
  const tabela = async () => ev(`(()=>{const d=document.querySelector('.a11y-table');return {resumo:d.querySelector('summary').textContent,coluna:d.querySelector('th').textContent,linhas:d.querySelectorAll('tbody tr').length};})()`);
  await filtrar('grain', 'year');
  let t = await tabela();
  log(t.resumo.includes('mensais') && t.coluna === 'MÊS' && t.linhas === 12, `ano: tabela mensal com 12 linhas (${t.coluna}, ${t.linhas})`);
  await filtrar('grain', 'month'); await filtrar('period', '2023-11');
  t = await tabela();
  log(t.resumo.includes('diários') && t.coluna === 'DIA' && t.linhas === 30, `mês: tabela diária com 30 linhas (${t.coluna}, ${t.linhas})`);
  await filtrar('grain', 'week'); await filtrar('period', '2023-W30');
  t = await tabela();
  log(t.resumo.includes('diários') && t.coluna === 'DIA' && t.linhas === 7, `semana: tabela diária com 7 linhas (${t.coluna}, ${t.linhas})`);

  // 2. a semana 53 para na cobertura da base
  await filtrar('compare', 'previous');
  await filtrar('period', '2023-W52');
  log(await ev("document.querySelectorAll('.chart .mark').length===7"), 'semana 52: sete dias');
  log(await ev("!!document.querySelector('.chart polyline[stroke-dasharray]')"), 'semana 52: compara com a anterior');
  await filtrar('period', '2023-W53');
  const parcial = await ev(`(()=>({marcas:document.querySelectorAll('.chart .mark').length,intervalo:rangeFor(),tracejada:!!document.querySelector('.chart polyline[stroke-dasharray]'),aviso:[...document.querySelectorAll('.panel-note')].some(n=>n.textContent.includes('Semana parcial')),rotulo:document.getElementById('period').selectedOptions[0].text}))()`);
  log(parcial.intervalo[1] === '2024-01-01', `semana 53: intervalo cortado na cobertura (${parcial.intervalo.join(' a ')})`);
  log(parcial.marcas === 1, `semana 53: desenha só o dia coberto (${parcial.marcas} marca)`);
  log(!parcial.tracejada, 'semana 53: não compara com uma semana cheia');
  log(parcial.aviso, 'semana 53: avisa que o recorte é parcial');
  log(/parcial/.test(parcial.rotulo), `semana 53: o seletor diz parcial ("${parcial.rotulo}")`);

  // 3. trocar de granularidade mantem onde o usuario estava
  await filtrar('grain', 'month'); await filtrar('period', '2023-07');
  await filtrar('grain', 'quarter');
  log(await ev("state.period==='2023-Q3'"), `julho vira trimestre 3 (${await ev('state.period')})`);
  await filtrar('grain', 'month');
  log(await ev("state.period==='2023-07'"), `trimestre 3 volta para julho (${await ev('state.period')})`);
  await filtrar('grain', 'week');
  log(await ev("state.period==='2023-W26'"), `julho vira a semana que o contém (${await ev('state.period')})`);

  // 4. as frentes de negocio funcionam tambem aqui, com leitura temporal
  log(await ev("!document.getElementById('fronts').hidden"), 'os chips de frente aparecem nesta seção');
  log(await ev("document.querySelectorAll('.front-chip').length===5"), 'as cinco frentes estão disponíveis');
  await ev(`[...document.querySelectorAll('.front-chip')].find(b=>b.textContent==='Marketing').click()`);
  let pronto = false;
  for (let i = 0; i < 90; i++) {if (await ev("document.querySelectorAll('.kpis-front .kpi').length>0")) {pronto = true; break;} await new Promise(r => setTimeout(r, 400));}
  log(pronto, 'Marketing renderiza ao ser selecionada em tendências');
  if (pronto) {
    log(await ev("document.querySelectorAll('.chart rect,.chart circle').length>=12"), 'gráfico com os doze meses da frente');
    log(await ev("!!document.getElementById('front-trend-kpi')"), 'seletor de KPI do gráfico da frente');
    log(await ev("document.querySelectorAll('.panel table tbody tr').length===12"), 'tabela mensal com doze linhas');
  }
  await ev(`[...document.querySelectorAll('.front-chip')].find(b=>b.textContent==='Estoque').click()`);
  for (let i = 0; i < 60; i++) {if (await ev("document.querySelectorAll('.kpis-front .kpi').length>0")) break; await new Promise(r => setTimeout(r, 400));}
  log(await ev("/não tem série temporal/i.test(document.getElementById('content').innerText)"), 'Estoque avisa que não tem série temporal');
  log(await ev("document.querySelectorAll('.chart').length===0"), 'Estoque não desenha gráfico vazio');
  await ev(`[...document.querySelectorAll('.front-chip')].find(b=>b.textContent==='Geral').click()`);
  for (let i = 0; i < 60; i++) {if (await ev("!document.querySelector('.kpis-front')")) break; await new Promise(r => setTimeout(r, 400));}
  log(await ev("/Compara..o por canal/i.test(document.getElementById('content').innerText)"), 'voltar para Geral restaura a tendência original');

  log(excecoes.length === 0, excecoes.length ? `excecoes: ${excecoes.join(' | ')}` : 'nenhuma excecao no console');
  console.log(`\n${falhou === 0 ? 'TENDENCIAS: TODAS AS VERIFICACOES PASSARAM' : `TENDENCIAS: ${falhou} FALHA(S)`}`);
} finally {
  ws?.close(); browser.kill();
}
process.exit(falhou === 0 ? 0 : 1);
