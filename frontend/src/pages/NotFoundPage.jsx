import { Link } from "react-router-dom";
import SiteFooter from "../components/layout/SiteFooter";

export default function NotFoundPage() {
  return (
    <div className="empty">
      <h2>페이지를 찾을 수 없습니다</h2>
      <Link className="link" to="/">
        홈으로
      </Link>
      <SiteFooter />
    </div>
  );
}
