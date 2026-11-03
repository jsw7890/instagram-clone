import { useEffect, useState } from "react";
import { Outlet, useLocation } from "react-router-dom";
import * as notifApi from "../../api/notifications";
import { useAuth } from "../../context/AuthContext";
import useRequireLogin from "../../hooks/useRequireLogin";
import CreatePost from "../post/CreatePost";
import BottomNav from "./BottomNav";
import MobileHeader from "./MobileHeader";
import Sidebar from "./Sidebar";
import SiteFooter from "./SiteFooter";

export default function AppShell() {
  const { user, loading } = useAuth();
  const requireLogin = useRequireLogin();
  const location = useLocation();
  const [create, setCreate] = useState(false);
  const [unread, setUnread] = useState(false);

  useEffect(() => {
    if (!user) {
      setUnread(false);
      return;
    }
    notifApi
      .listNotifications()
      .then((d) => setUnread(d.has_unread))
      .catch(() => {});
  }, [user, location.pathname]);

  const onCreate = () => {
    if (!requireLogin()) return;
    setCreate(true);
  };

  if (loading) return <div className="spinner" />;

  return (
    <div className="app-shell">
      <Sidebar onCreate={onCreate} unread={unread} />
      <main className="main">
        <MobileHeader />
        <Outlet context={{ openCreate: onCreate }} />
        <SiteFooter />
      </main>
      <BottomNav onCreate={onCreate} />
      {create && <CreatePost onClose={() => setCreate(false)} />}
    </div>
  );
}
