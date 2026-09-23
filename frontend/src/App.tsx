import { BrowserRouter, Routes, Route, Navigate, Outlet } from "react-router-dom"
import { useAuthStore } from "@/store/auth"
import Layout from "@/components/Layout"
import ProtectedRoute from "@/components/ProtectedRoute"
import Login from "@/pages/Login"
import Dashboard from "@/pages/Dashboard"
import TIList from "@/pages/TIList"
import TIDetail from "@/pages/TIDetail"
import Sessions from "@/pages/Sessions"
import Notifications from "@/pages/Notifications"
import Reports from "@/pages/Reports"
import Users from "@/pages/Users"
import UserDetail from "@/pages/UserDetail"
import Profile from "@/pages/Profile"
import TIDocuments from "@/pages/TIDocuments"
import Assignments from "@/pages/Assignments"
import AdvanceRegister from "@/pages/AdvanceRegister"
import MilestoneApproval from "@/pages/MilestoneApproval"
import Evaluations from "@/pages/Evaluations"
import Programs from "@/pages/Programs"
import NotFound from "@/pages/NotFound"

function LayoutWrapper() {
  return (
    <ProtectedRoute>
      <Layout><Outlet /></Layout>
    </ProtectedRoute>
  )
}

export default function App() {
  const { isAuthenticated } = useAuthStore()
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={isAuthenticated() ? <Navigate to="/dashboard" replace /> : <Login />} />
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
        <Route element={<LayoutWrapper />}>
          <Route path="/dashboard"     element={<Dashboard />} />
          <Route path="/ti"            element={<TIList />} />
          <Route path="/ti/:id"             element={<TIDetail />} />
          <Route path="/ti/:id/documents"   element={<ProtectedRoute><TIDocuments /></ProtectedRoute>} />
          <Route path="/users/:id"          element={<ProtectedRoute><UserDetail /></ProtectedRoute>} />
          <Route path="/evaluations"  element={<ProtectedRoute><Evaluations /></ProtectedRoute>} />
          <Route path="/programs"     element={<ProtectedRoute><Programs /></ProtectedRoute>} />
          <Route path="/assignments"  element={<ProtectedRoute roles={["ADM","COO","DIR","TUT","EST"]}><Assignments /></ProtectedRoute>} />
          <Route path="/advances"     element={<ProtectedRoute roles={["EST","TUT"]}><AdvanceRegister /></ProtectedRoute>} />
          <Route path="/milestones"   element={<ProtectedRoute roles={["EST","TUT","COO","DIR"]}><MilestoneApproval /></ProtectedRoute>} />
          <Route path="/sessions"           element={<Sessions />} />
          <Route path="/notifications" element={<Notifications />} />
          <Route path="/profile"        element={<ProtectedRoute><Profile /></ProtectedRoute>} />
          <Route path="/users"         element={<ProtectedRoute roles={["ADM","COO","DIR"]}><Users /></ProtectedRoute>} />
          <Route path="/reports"       element={<ProtectedRoute roles={["ADM","COO","DIR"]}><Reports /></ProtectedRoute>} />
        </Route>
        <Route path="*" element={<NotFound />} />
      </Routes>
    </BrowserRouter>
  )
}
