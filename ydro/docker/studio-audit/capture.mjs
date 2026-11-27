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
  const expected=['desktop','mobile'].flatMap(d=>{
    const film=checks.find(c=>c.name===d)?.film;
    return [
      ...[0,25,50,75,100].map(n=>d+'-'+n+'.png'),
      ...['home','about','services','benefits','contacts'].map(s=>d+'-section-'+s+'.png'),
      ...(film?.enabled?[0,50,100].map(n=>d+'-hero-film-'+n+'.png'):[]),
      ...(d==='desktop'&&film?.enabled&&film?.pinned?['desktop-hero-film-short.png']:[])
    ];
  });
  const expectedSet=new Set(expected);
  const counts=new Map();
  for(const s of report.screenshots)counts.set(s.file,(counts.get(s.file)||0)+1);
  report.missingScreenshots=expected.filter(file=>!report.screenshots.some(s=>s.file===file&&s.ok===true));
  report.unexpectedScreenshots=[...counts.keys()].filter(file=>!expectedSet.has(file));
  report.duplicateScreenshots=[...counts].filter(([,n])=>n!==1).map(([file])=>file);
  report.screenshotsComplete=report.screenshotFailures.length===0&&
    report.missingScreenshots.length===0&&report.unexpectedScreenshots.length===0&&
    report.duplicateScreenshots.length===0&&report.screenshots.every(s=>s.ok===true);
  report.passed=report.functionalPassed&&report.screenshotsComplete;
  return report;
}
