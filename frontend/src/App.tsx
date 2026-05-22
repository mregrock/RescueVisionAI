import { Navigate, Route, Routes } from 'react-router-dom'
import { Layout } from './components/Layout'
import { AnalyzePage } from './pages/AnalyzePage'
import { CameraPage } from './pages/CameraPage'
import { ProtocolDetailPage } from './pages/ProtocolDetailPage'
import { ProtocolsListPage } from './pages/ProtocolsListPage'

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route index element={<AnalyzePage />} />
        <Route path="protocols" element={<ProtocolsListPage />} />
        <Route path="protocols/:id" element={<ProtocolDetailPage />} />
        <Route path="camera" element={<CameraPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  )
}
