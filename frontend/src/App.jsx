import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import AppShell from "./components/layout/AppShell";
import ProtectedRoute from "./components/common/ProtectedRoute";
import { AuthProvider } from "./context/AuthContext";
import { ToastProvider } from "./context/ToastContext";
import ActivityPage from "./pages/ActivityPage";
import AdminDashboard from "./pages/admin/AdminDashboard";
import AdminLoginPage from "./pages/admin/AdminLoginPage";
import AdminPostsPage from "./pages/admin/AdminPostsPage";
import AdminUsersPage from "./pages/admin/AdminUsersPage";
import AdminLayout from "./components/admin/AdminLayout";
import AdminRoute from "./components/common/AdminRoute";
import { DirectListPage, DirectThreadPage } from "./pages/DirectPages";
import ExplorePage from "./pages/ExplorePage";
import FeedPage from "./pages/FeedPage";
import LoginPage from "./pages/LoginPage";
import NotFoundPage from "./pages/NotFoundPage";
import PostDetailPage from "./pages/PostDetailPage";
import ProfilePage from "./pages/ProfilePage";
import SearchPage from "./pages/SearchPage";
import { PasswordSettings, PrivacySettings, SettingsHome } from "./pages/SettingsPages";
import SignupPage from "./pages/SignupPage";

export default function App() {
  return (
    <AuthProvider>
      <ToastProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/login" element={<LoginPage />} />
            <Route path="/signup" element={<SignupPage />} />
            <Route path="/admin/login" element={<AdminLoginPage />} />
            <Route element={<AdminRoute />}>
              <Route element={<AdminLayout />}>
                <Route path="/admin" element={<AdminDashboard />} />
                <Route path="/admin/users" element={<AdminUsersPage />} />
                <Route path="/admin/posts" element={<AdminPostsPage />} />
              </Route>
            </Route>
            <Route element={<AppShell />}>
              <Route path="/" element={<FeedPage />} />
              <Route path="/explore" element={<ExplorePage />} />
              <Route path="/search" element={<SearchPage />} />
              <Route path="/p/:postId" element={<PostDetailPage />} />
              <Route element={<ProtectedRoute />}>
                <Route path="/direct" element={<DirectListPage />} />
                <Route path="/direct/:conversationId" element={<DirectThreadPage />} />
                <Route path="/activity" element={<ActivityPage />} />
                <Route path="/settings" element={<SettingsHome />} />
                <Route path="/settings/password" element={<PasswordSettings />} />
                <Route path="/settings/privacy" element={<PrivacySettings />} />
                <Route path="/:username/saved" element={<ProfilePage savedOnly />} />
              </Route>
              <Route path="/:username" element={<ProfilePage />} />
            </Route>
            <Route path="/not-found" element={<NotFoundPage />} />
            <Route path="*" element={<Navigate to="/not-found" replace />} />
          </Routes>
        </BrowserRouter>
      </ToastProvider>
    </AuthProvider>
  );
}
