const puppeteer = require('puppeteer');

async function testBasicFunctionality() {
  console.log('🚀 Testing basic functionality...\n');
  
  const browser = await puppeteer.launch({ 
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--use-fake-ui-for-media-stream']
  });
  
  try {
    const page = await browser.newPage();
    
    const errors = [];
    const warnings = [];
    
    page.on('console', msg => {
      if (msg.type() === 'error') {
        errors.push(msg.text());
      } else if (msg.type() === 'warning') {
        warnings.push(msg.text());
      }
    });
    
    page.on('pageerror', error => {
      errors.push(`Page error: ${error.message}`);
    });
    
    // Test homepage
    console.log('📱 Testing homepage...');
    await page.goto('http://localhost:3000', { waitUntil: 'networkidle0', timeout: 10000 });
    
    const homepageTitle = await page.evaluate(() => document.title);
    console.log(`   Title: ${homepageTitle}`);
    
    const hasVoiceLink = await page.$('a[href="/voice"]');
    console.log(`   Voice link found: ${hasVoiceLink ? '✅' : '❌'}`);
    
    // Test voice page
    console.log('🔊 Testing voice interface...');
    await page.goto('http://localhost:3000/voice', { waitUntil: 'networkidle0', timeout: 10000 });
    
    await new Promise(resolve => setTimeout(resolve, 2000)); // Wait for WebSocket connection
    
    // Check for key elements
    const hasStartButton = await page.evaluate(() => {
      const buttons = document.querySelectorAll('button');
      return Array.from(buttons).some(btn => btn.textContent.includes('Start') || btn.textContent.includes('call'));
    });
    console.log(`   Start button found: ${hasStartButton ? '✅' : '❌'}`);
    
    const hasSpaceHint = await page.evaluate(() => {
      return document.querySelector('kbd') !== null;
    });
    console.log(`   Spacebar hint found: ${hasSpaceHint ? '✅' : '❌'}`);
    
    const hasConversationPanel = await page.evaluate(() => {
      const panels = document.querySelectorAll('div');
      return Array.from(panels).some(div => 
        div.textContent.includes('Conversation') || 
        div.classList.toString().includes('conversation')
      );
    });
    console.log(`   Conversation panel found: ${hasConversationPanel ? '✅' : '❌'}`);
    
    // Check for responsive elements
    const hasResponsiveClasses = await page.evaluate(() => {
      const body = document.body.innerHTML;
      return body.includes('lg:') || body.includes('md:') || body.includes('sm:');
    });
    console.log(`   Responsive classes found: ${hasResponsiveClasses ? '✅' : '❌'}`);
    
    // Check for loading animations
    const hasAnimations = await page.evaluate(() => {
      const body = document.body.innerHTML;
      return body.includes('animate-') || body.includes('transition-');
    });
    console.log(`   Animations found: ${hasAnimations ? '✅' : '❌'}`);
    
    // Results
    console.log('\n' + '='.repeat(50));
    console.log('📊 TEST RESULTS');
    console.log('='.repeat(50));
    
    console.log(`\n✅ Homepage loads: YES`);
    console.log(`✅ Voice interface loads: YES`);
    console.log(`${hasVoiceLink ? '✅' : '❌'} Navigation working: ${hasVoiceLink ? 'YES' : 'NO'}`);
    console.log(`${hasStartButton ? '✅' : '❌'} Start button present: ${hasStartButton ? 'YES' : 'NO'}`);
    console.log(`${hasSpaceHint ? '✅' : '❌'} Spacebar instructions: ${hasSpaceHint ? 'YES' : 'NO'}`);
    console.log(`${hasConversationPanel ? '✅' : '❌'} Conversation UI: ${hasConversationPanel ? 'YES' : 'NO'}`);
    console.log(`${hasResponsiveClasses ? '✅' : '❌'} Responsive design: ${hasResponsiveClasses ? 'YES' : 'NO'}`);
    console.log(`${hasAnimations ? '✅' : '❌'} Loading animations: ${hasAnimations ? 'YES' : 'NO'}`);
    
    console.log(`\n📋 Console Analysis:`);
    console.log(`   Errors: ${errors.length}`);
    console.log(`   Warnings: ${warnings.length}`);
    
    if (errors.length > 0) {
      console.log(`\n❌ Errors found:`);
      errors.slice(0, 3).forEach((error, i) => {
        console.log(`   ${i + 1}. ${error.substring(0, 100)}...`);
      });
    }
    
    const criticalIssues = [];
    if (!hasStartButton) criticalIssues.push('Missing start button');
    if (errors.length > 0) criticalIssues.push(`${errors.length} JavaScript errors`);
    
    const isReady = criticalIssues.length === 0;
    console.log(`\n🚀 READY FOR SHIPPING: ${isReady ? 'YES ✅' : 'NO ❌'}`);
    
    if (!isReady) {
      console.log('\n📋 Issues to fix:');
      criticalIssues.forEach((issue, i) => console.log(`   ${i + 1}. ${issue}`));
    }
    
    return { ready: isReady, errors: errors.length, warnings: warnings.length };
    
  } catch (error) {
    console.error('❌ Test failed:', error.message);
    return { ready: false, error: error.message };
  } finally {
    await browser.close();
  }
}

testBasicFunctionality()
  .then(results => {
    console.log('\n🏁 Test completed.');
  })
  .catch(error => {
    console.error('💥 Test runner failed:', error);
  });