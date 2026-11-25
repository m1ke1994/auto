// Bounded screenshot capture. Never fabricate a successful screenshot.
export function createCapture(report,{now=Date.now,budgetMs=240000,timeouts=[30000,45000],log=console.log}={}){
  let used=0;
  report.screenshots=[];
  report.screenshotFailures=[];
  return async function capture(page,file){
    const record={file,attempts:0,ok:false};
    let error='Screenshot time budget exhausted';
    for(const limit of timeouts){
      const remaining=budgetMs-used;
      if(remaining<=0)break;
      const timeout=Math.max(1,Math.min(limit,remaining));
      record.attempts++;
      const started=now();
      try{
        log('AUDIT_SCREENSHOT: '+file+' attempt='+record.attempts+' timeout='+timeout);
        await page.screenshot({path:'/report/'+file,timeout});
        record.ok=true;
        break;
      }catch(e){
        error=String(e).slice(0,700);
        // Retry only a timeout, not a closed browser or filesystem error.
        if(e?.name!=='TimeoutError'&&!/timeout.*exceeded/i.test(error))break;
      }finally{
        used+=Math.max(0,now()-started);
      }
    }
    if(!record.ok){
      record.error=error;
      report.screenshotFailures.push({file,error,attempts:record.attempts});
      log('AUDIT_SCREENSHOT_FAILED: '+file+'; '+error);
    }
    report.screenshots.push(record);
    return record.ok;
  };
}
export function finalizeAudit(report){
  const checks=report.checks;
  report.functionalPassed=!report.error&&checks.length===2&&
    new Set(checks.map(c=>c.name)).size===2&&
    checks.every(c=>['desktop','mobile'].includes(c.name)&&Object.keys(c.checks).length>0&&Object.values(c.checks).every(v=>v===true));
  const expected=['desktop','mobile'].flatMap(d=>[
    ...[0,25,50,75,100].map(n=>d+'-'+n+'.png'),
    ...['home','about','services','benefits','contacts'].map(s=>d+'-section-'+s+'.png')
  ]);
  report.screenshotsComplete=report.screenshotFailures.length===0&&
    report.screenshots.length===expected.length&&
    expected.every(file=>report.screenshots.some(s=>s.file===file&&s.ok===true));
  report.passed=report.functionalPassed&&report.screenshotsComplete;
  return report;
}
