import { NavLink, Routes, Route } from 'react-router-dom'
import ClaimsQueue from './pages/ClaimsQueue'
import NewClaim from './pages/NewClaim'
import PolicyAdmin from './pages/PolicyAdmin'
import ReviewWorkspace from './pages/ReviewWorkspace'

export default function App() {
  return (
    <div className="app">
      <header className="app-header">
        <div className="container">
          <div className="brand">
            <h1>ClaimSense AI</h1>
            <p>AI assists → adjuster reviews → adjuster decides</p>
          </div>
          <nav className="nav">
            <NavLink to="/" end>Queue</NavLink>
            <NavLink to="/new">New claim</NavLink>
            <NavLink to="/policies">Policies</NavLink>
          </nav>
        </div>
      </header>
      <main className="container page">
        <Routes>
          <Route path="/" element={<ClaimsQueue />} />
          <Route path="/new" element={<NewClaim />} />
          <Route path="/policies" element={<PolicyAdmin />} />
          <Route path="/claims/:claimId/review" element={<ReviewWorkspace />} />
        </Routes>
      </main>
    </div>
  )
}
