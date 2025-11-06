import { useState } from 'react'
import proscientiaLogo from "./assets/logo-transparent-white.png"
import './App.css'

function App() {
  const [count, setCount] = useState(0)

  return (
    <>
      <div>
        <img src={proscientiaLogo} className="logo" alt="Vite logo" />
        <div className="p-6 rounded-2xl shadow-xl bg-white">
          <h1 className="text-2xl font-bold text-zinc-800">Frontend działa 🚀</h1>
          <p className="text-gray-600">Vite + React + TS + TailwindCSS</p>
        </div>
      </div>
    </>
  )
}

export default App
