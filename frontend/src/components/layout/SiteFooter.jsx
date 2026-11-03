export default function SiteFooter() {
  return (
    <footer className="site-footer">
      <nav className="site-footer-links" aria-label="사이트 정보">
        <span>소개</span>
        <span>블로그</span>
        <span>채용</span>
        <span>도움말</span>
        <span>API</span>
        <span>개인정보처리방침</span>
        <span>이용약관</span>
        <span>위치</span>
        <span>한국어</span>
      </nav>
      <p>
        주식회사 인스타클론 · 대표 한서윤 · 서울특별시 강남구 테헤란로 123, 4층
      </p>
      <p>
        사업자등록번호 123-45-67890 · 통신판매업 2026-서울강남-0123 · 문의 support@igclone.local
      </p>
      <p className="site-footer-copy">© 2026 Instagram from Meta · 학습용 클론</p>
    </footer>
  );
}
