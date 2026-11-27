import {test} from 'node:test';
import assert from 'node:assert/strict';
import {createCapture,finalizeAudit} from './capture.mjs';

const timeout=()=>Object.assign(new Error('Timeout exceeded'),{name:'TimeoutError'});
const options={log:()=>{}};
test('timeout retries and successful frame is recorded',async()=>{
  const report={};let calls=0;
  const shot=createCapture(report,options);
  const page={screenshot:async({timeout:t})=>{
    calls++;assert.equal(t,calls===1?30000:45000);
    if(calls===1)throw timeout();
  }};
  assert.equal(await shot(page,'desktop-0.png'),true);
  assert.equal(calls,2);
  assert.equal(report.screenshotFailures.length,0);
  assert.equal(report.screenshots[0].attempts,2);
});
test('failed frame does not abort subsequent capture',async()=>{
  const report={};const shot=createCapture(report,options);
  assert.equal(await shot({screenshot:async()=>{throw timeout();}},'desktop-0.png'),false);
  assert.equal(report.screenshotFailures[0].attempts,2);
  assert.equal(await shot({screenshot:async()=>{}},'desktop-25.png'),true);
  assert.equal(report.screenshots.length,2);
});
test('non-timeout errors are not retried',async()=>{
  const report={};let calls=0;
  const shot=createCapture(report,options);
  await shot({screenshot:async()=>{calls++;throw Error('Target closed');}},'desktop-0.png');
  assert.equal(calls,1);
  assert.equal(report.screenshotFailures.length,1);
});
test('total time budget bounds subsequent captures',async()=>{
  const report={};let clock=0,calls=0;
  const shot=createCapture(report,{...options,budgetMs:35,timeouts:[30,45],now:()=>clock});
  const page={screenshot:async({timeout:t})=>{calls++;clock+=t;throw timeout();}};
  await shot(page,'desktop-0.png');
  await shot(page,'desktop-25.png');
  assert.equal(clock,35);
  assert.equal(calls,2);
  assert.equal(report.screenshotFailures[1].attempts,0);
});
test('functional success cannot hide missing screenshots or failed checks',()=>{
  const report={checks:['desktop','mobile'].map(name=>({name,checks:{rendered:true}})),screenshots:[],screenshotFailures:[]};
  finalizeAudit(report);
  assert.equal(report.functionalPassed,true);
  assert.equal(report.passed,false);
  report.screenshots=['desktop','mobile'].flatMap(d=>[
    ...[0,25,50,75,100].map(n=>d+'-'+n+'.png'),
    ...['home','about','services','benefits','contacts'].map(s=>d+'-section-'+s+'.png')
  ]).map(file=>({file,ok:true}));
  finalizeAudit(report);
  assert.equal(report.passed,true);
  report.screenshotFailures.push({file:'desktop-0.png'});
  finalizeAudit(report);
  assert.equal(report.passed,false);
  report.screenshotFailures=[];
  report.checks[1].checks.rendered=false;
  finalizeAudit(report);
  assert.equal(report.functionalPassed,false);
  assert.equal(report.passed,false);
});

function filmReport(pinned=true){
  const checks=['desktop','mobile'].map(name=>({name,checks:{rendered:true,heroFilm:true},film:{enabled:true,pinned}}));
  const screenshots=checks.flatMap(({name:d})=>[
    ...[0,25,50,75,100].map(n=>d+'-'+n+'.png'),
    ...['home','about','services','benefits','contacts'].map(s=>d+'-section-'+s+'.png'),
    ...[0,50,100].map(n=>d+'-hero-film-'+n+'.png'),
    ...(d==='desktop'&&pinned?['desktop-hero-film-short.png']:[])
  ]).map(file=>({file,ok:true}));
  return {checks,screenshots,screenshotFailures:[]};
}
test('pinned 360 film requires and accepts exactly 27 successful screenshots',()=>{
  const report=filmReport();
  assert.equal(report.screenshots.length,27);
  finalizeAudit(report);
  assert.equal(report.functionalPassed,true);
  assert.equal(report.screenshotsComplete,true);
  assert.equal(report.passed,true);
  assert.deepEqual(report.missingScreenshots,[]);
  report.screenshots=report.screenshots.filter(s=>s.file!=='desktop-hero-film-short.png');
  finalizeAudit(report);
  assert.equal(report.passed,false);
  assert.deepEqual(report.missingScreenshots,['desktop-hero-film-short.png']);
});
test('legacy film accepts 26 screenshots without a short viewport capture',()=>{
  const report=filmReport(false);
  assert.equal(report.screenshots.length,26);
  assert.equal(finalizeAudit(report).passed,true);
});
test('film screenshots do not conceal failed checks, duplicates or unknown frames',()=>{
  const report=filmReport();
  report.checks[1].checks.heroFilm=false;
  assert.equal(finalizeAudit(report).passed,false);
  assert.equal(report.screenshotsComplete,true);
  report.checks[1].checks.heroFilm=true;
  report.screenshots.push({...report.screenshots[0]});
  assert.equal(finalizeAudit(report).passed,false);
  assert.deepEqual(report.duplicateScreenshots,['desktop-0.png']);
  report.screenshots.pop();
  report.screenshots.push({file:'unknown.png',ok:true});
  assert.equal(finalizeAudit(report).passed,false);
  assert.deepEqual(report.unexpectedScreenshots,['unknown.png']);
  report.screenshots.pop();
  report.screenshots.find(s=>s.file==='mobile-hero-film-50.png').ok=false;
  assert.equal(finalizeAudit(report).passed,false);
  assert.deepEqual(report.missingScreenshots,['mobile-hero-film-50.png']);
});
