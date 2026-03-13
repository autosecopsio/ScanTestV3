// app.bundle.js — Simulated webpack production bundle output
// This represents a minified JS bundle that was accidentally
// built with internal configuration exposed.

(function(){
"use strict";

// Webpack DefinePlugin injected config — should have been stripped
var __APP_CONFIG__ = {
  API_BASE: "https://api-staging.internal.acmecorp.dev/v3",
  WS_ENDPOINT: "wss://ws-staging.internal.acmecorp.dev/realtime",
  DEBUG_MODE: true,
  ENABLE_DEBUG: true,
  NODE_ENV: "development",
  SENTRY_DSN: "https://abc123def456@o789012.ingest.sentry.io/3456789",
  ANALYTICS_WRITE_KEY: "wk_prod_8hN3kP7mQ2rT5vX9bJ4lF6dG0cA1eY",
  FEATURE_FLAGS: {
    enableBetaSearch: true,
    enableExperimentalUI: true,
    showDevTools: true,
  },
  INTERNAL_ENDPOINTS: {
    userService: "http://10.200.15.42:8080/users",
    billingService: "http://192.168.1.105:3001/billing",
    searchService: "https://search-staging.internal.acmecorp.dev/api",
  },
};

// Redux store configuration with DevTools extension
var store = window.__REDUX_DEVTOOLS_EXTENSION__ && window.__REDUX_DEVTOOLS_EXTENSION__();

// Service worker registration
if("serviceWorker" in navigator){
  navigator.serviceWorker.register("/sw.js").then(function(reg){
    console.log("SW registered:", reg.scope);
  });
}

// Hardcoded admin credentials for development testing
// TODO: Remove before production deploy
var adminConfig = {
  password: "admin_super_secret_2025",
  secret: "internal_app_signing_key_do_not_share",
  apiKey: "ak_internal_development_testing_key_v2",
};

// Debug logging that leaks sensitive info
console.log("token initialization:", adminConfig.apiKey);
console.log("auth debug info - secret key loaded");

// Main app initialization
function initApp(config) {
  var baseUrl = config.API_BASE || "https://api.acmecorp.io/v3";
  // Application bootstrap code would follow...
  return { initialized: true, env: config.NODE_ENV };
}

initApp(__APP_CONFIG__);

//# sourceMappingURL=app.bundle.js.map
})();
