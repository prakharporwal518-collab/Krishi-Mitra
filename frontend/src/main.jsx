import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.jsx'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')).render(<App />)

// When a new version of the app (and model) is deployed, the offline service worker installs it in the
// background. Reload once when it takes over, so people never keep running an old version.
if ('serviceWorker' in navigator) {
  const hadController = !!navigator.serviceWorker.controller // false on the very first visit: no reload then
  let reloaded = false
  navigator.serviceWorker.addEventListener('controllerchange', () => {
    if (hadController && !reloaded) { reloaded = true; window.location.reload() }
  })
}
