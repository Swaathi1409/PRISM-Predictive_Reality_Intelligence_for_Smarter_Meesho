/**
 * main.jsx — React 18 entry point.
 *
 * Library: react-dom (MIT). Uses createRoot for React 18 concurrent mode.
 */

import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.jsx'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
)
