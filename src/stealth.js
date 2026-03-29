// Stealth patches for headless Chromium
// Injected before page scripts via @playwright/mcp --init-script

// 1. Override navigator.webdriver
Object.defineProperty(navigator, 'webdriver', { get: () => false });

// 2. Override chrome runtime (headless detection)
window.chrome = { runtime: {}, loadTimes: function(){}, csi: function(){} };

// 3. Override permissions API
const originalQuery = window.navigator.permissions.query;
window.navigator.permissions.query = (parameters) => (
  parameters.name === 'notifications' ?
    Promise.resolve({ state: Notification.permission }) :
    originalQuery(parameters)
);

// 4. Override plugins (headless has 0 plugins)
Object.defineProperty(navigator, 'plugins', {
  get: () => [
    { name: 'Chrome PDF Plugin', filename: 'internal-pdf-viewer' },
    { name: 'Chrome PDF Viewer', filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai' },
    { name: 'Native Client', filename: 'internal-nacl-plugin' },
  ],
});

// 5. Override languages
Object.defineProperty(navigator, 'languages', {
  get: () => ['en-US', 'en'],
});

// 6. Fix WebGL renderer (headless shows "Google SwiftShader")
const getParameterOrig = WebGLRenderingContext.prototype.getParameter;
WebGLRenderingContext.prototype.getParameter = function(parameter) {
  if (parameter === 37445) return 'Intel Inc.';
  if (parameter === 37446) return 'Intel Iris OpenGL Engine';
  return getParameterOrig.call(this, parameter);
};
