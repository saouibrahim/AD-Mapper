import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import ReconPage from './pages/ReconPage'
import GraphPage from './pages/GraphPage'
import MisconfigsPage from './pages/MisconfigsPage'
import AttackPathsPage from './pages/AttackPathsPage'
import ReportsPage from './pages/ReportsPage'

export default function App() {
  return (
    <BrowserRouter>
      <Toaster
        position="top-right"
        toastOptions={{
          style: {
            background: '#13131f',
            color: '#e2e8f0',
            border: '1px solid #2a2a45',
            fontFamily: "'Share Tech Mono', monospace",
            fontSize: '13px',
          },
        }}
      />
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Navigate to="/dashboard" replace />} />
          <Route path="dashboard" element={<Dashboard />} />
          <Route path="recon" element={<ReconPage />} />
          <Route path="graph" element={<GraphPage />} />
          <Route path="misconfigs" element={<MisconfigsPage />} />
          <Route path="attack-paths" element={<AttackPathsPage />} />
          <Route path="reports" element={<ReportsPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}
