// Revisao local no Edge headless: nao requer bibliotecas externas.
import {spawn} from 'node:child_process';
import {mkdir,writeFile} from 'node:fs/promises';
import {resolve} from 'node:path';
import {pathToFileURL} from 'node:url';
import assert from 'node:assert/strict';
const folder=resolve('prototype-review');
await mkdir(folder,{recursive:true});
const browser=spawn('C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',[
  '--headless=new','--disable-gpu','--no-first-run','--no-default-browser-check',
  '--remote-debugging-port=9337',`--user-data-dir=${folder}/edge-profile`,'about:blank'
],{windowsHide:true,stdio:'ignore'});
let ws;
try {
  let tabs;
  for(let i=0;i<50;i++){
    try {tabs=await (await fetch('http://127.0.0.1:9337/json')).json();if(tabs.some(t=>t.type==='page'))break;}catch{}
    await new Promise(r=>setTimeout(r,200));
  }
  assert(tabs,'Edge nao abriu a porta de depuracao');
  ws=new WebSocket(tabs.find(t=>t.type==='page').webSocketDebuggerUrl);
  await new Promise((res,rej)=>{ws.onopen=res;ws.onerror=rej;});
  let id=0;const pending=new Map();const errors=[];
  ws.onmessage=e=>{const m=JSON.parse(e.data);if(m.id){const p=pending.get(m.id);pending.delete(m.id);m.error?p.reject(m.error):p.resolve(m.result);}if(m.method==='Runtime.exceptionThrown')errors.push(m.params.exceptionDetails);};
  const send=(method,params={})=>new Promise((resolve,reject)=>{const n=++id;pending.set(n,{resolve,reject});ws.send(JSON.stringify({id:n,method,params}));});
  const evaluate=async expression=>{const r=await send('Runtime.evaluate',{expression,returnByValue:true,awaitPromise:true});assert(!r.exceptionDetails,JSON.stringify(r.exceptionDetails));return r.result.value;};
  await send('Runtime.enable');await send('Page.enable');
  await send('Emulation.setDeviceMetricsOverride',{width:1440,height:1050,deviceScaleFactor:1,mobile:false});
  await send('Page.navigate',{url:pathToFileURL(resolve('docs/prototipo/index.html')).href});
  for(let i=0;i<50;i++){if(await evaluate("document.querySelectorAll('.kpi').length===5"))break;await new Promise(r=>setTimeout(r,100));}
  assert.equal(await evaluate("document.querySelectorAll('.kpi').length"),5);
  assert.equal(await evaluate('Math.round(aggregate(rows()).revenue*100)'),1596634087);
  assert.equal(await evaluate('aggregate(rows()).orders'),23388);
  await evaluate("document.querySelector('[data-metric=rate]').click()");
  assert.equal(await evaluate("document.getElementById('detail').open"),true);
  await evaluate("document.getElementById('close').click(); document.getElementById('channel').value='Marketplace'; document.getElementById('channel').dispatchEvent(new Event('change'))");
  assert.equal(await evaluate('Math.round(aggregate(rows()).revenue*100)'),338299220);
  await evaluate("document.getElementById('period').value='12';document.getElementById('period').dispatchEvent(new Event('change'));document.getElementById('ai').click()");
  assert.equal(await evaluate("document.getElementById('drawer-content').textContent.includes('52,44%')"),true);
  await evaluate("document.getElementById('close').click()");
  for(const section of ['tendencias','alertas','oportunidades','acoes','resultados','hipoteses','relatorio']){
    await evaluate(`document.querySelector('#nav [data-nav="${section}"]').click()`);
    assert.equal(await evaluate('state.section'),section);
    assert((await evaluate("document.getElementById('content').textContent.length"))>100);
  }
  await evaluate("navigate('resultados');document.querySelector('[data-simulation]').click()");
  assert.equal(await evaluate("document.getElementById('content').textContent.includes('SIMULAÇÃO')"),true);
  await evaluate("document.getElementById('reset').click();navigate('saude')");
  assert.equal(await evaluate('document.documentElement.scrollWidth>innerWidth'),false);
  const screenshot=await send('Page.captureScreenshot',{format:'png',captureBeyondViewport:true});
  await writeFile(resolve(folder,'dashboard-desktop.png'),Buffer.from(screenshot.data,'base64'));
  await send('Emulation.setDeviceMetricsOverride',{width:390,height:844,deviceScaleFactor:1,mobile:true});
  assert.equal(await evaluate('document.documentElement.scrollWidth>innerWidth'),false);
  const mobile=await send('Page.captureScreenshot',{format:'png',captureBeyondViewport:true});
  await writeFile(resolve(folder,'dashboard-mobile.png'),Buffer.from(mobile.data,'base64'));
  assert.equal(errors.length,0,JSON.stringify(errors));
  console.log(JSON.stringify({navigation:8,kpis:5,filters:'OK',drawer:'OK',contextual_demo:'OK',simulation:'OK',horizontal_overflow:false,runtime_errors:errors.length,screenshots:folder}));
  await send('Browser.close');
} finally {
  if(ws)ws.close();browser.kill();
}
