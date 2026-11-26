import { chromium } from 'playwright'

const base=process.env.STUDIO_URL||'http://127.0.0.1:8001'
const email=process.env.STUDIO_TEST_EMAIL,password=process.env.STUDIO_TEST_PASSWORD
const name=process.env.STUDIO_PROJECT_NAME,prompt=process.env.STUDIO_PROJECT_PROMPT
const profile=process.env.STUDIO_PROJECT_PROFILE||'cinema'
const hero=process.env.STUDIO_PROJECT_HERO||'auto'
const assetStyle=process.env.STUDIO_PROJECT_ASSET_STYLE||'realistic'
const requireModel=/^(1|true|yes)$/i.test(process.env.STUDIO_PROJECT_REQUIRE_MODEL||'false')
if(!email||!password||!name||!prompt)throw new Error('Credentials, project name and prompt are required')
const browser=await chromium.launch({headless:true})
const page=await browser.newPage({viewport:{width:1440,height:1000}})
page.setDefaultTimeout(20000)
try{
  console.log('QUEUE_BROWSER: login')
  await page.goto(`${base}/login?redirect=/studio`,{waitUntil:'networkidle'})
  await page.locator('#auth-email').fill(email);await page.locator('#auth-password').fill(password)
  await Promise.all([page.waitForURL('**/studio'),page.locator('button[type="submit"]').click()])
  console.log('QUEUE_BROWSER: studio ready')
  await page.locator('.studio').waitFor()
  await page.locator('.projects button').last().click()
  const form=page.locator('form.create-form')
  await form.waitFor()
  await form.locator('select').nth(0).selectOption('cinematic')
  await form.locator('select').nth(1).selectOption(profile)
  await form.locator('input[required]').fill(name)
  await form.locator('textarea[required]').fill(prompt)
  await form.locator('select').nth(2).selectOption(hero)
  await form.locator('select').nth(3).selectOption(assetStyle)
  if(requireModel)await form.locator('input[type="checkbox"]').check()
  console.log('QUEUE_BROWSER: submit')
  const [response]=await Promise.all([
    page.waitForResponse(r=>r.url().includes('/api/studio/projects/')&&r.request().method()==='POST',{timeout:30000}),
    form.locator('button').last().click(),
  ])
  const body=await response.json()
  if(response.status()!==202)throw new Error(`Queue failed: ${response.status()} ${JSON.stringify(body)}`)
  await page.locator('.status-card').waitFor({state:'visible'})
  console.log(JSON.stringify({status:response.status(),projectId:body.id,generationStatus:body.generation_status,name:body.name},null,2))
}finally{await browser.close()}
