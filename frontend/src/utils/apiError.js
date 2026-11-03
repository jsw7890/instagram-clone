const FIELD_LABELS = {
  email: "이메일",
  username: "사용자 이름",
  password: "비밀번호",
  full_name: "성명",
};

function validationEntryMessage(entry) {
  const raw = entry.msg || entry.message || "";
  if (raw.includes("Value error,")) {
    return raw.replace(/^Value error,\s*/, "");
  }
  const field = entry.loc?.[entry.loc.length - 1];
  const label = FIELD_LABELS[field] || field;
  if (entry.type === "string_pattern_mismatch" && field === "username") {
    return "사용자 이름은 영문, 숫자, 밑줄(_), 마침표(.)만 1~30자까지 사용할 수 있습니다";
  }
  if (entry.type === "string_too_short" && field === "password") {
    return "비밀번호는 8자 이상이어야 합니다";
  }
  if (entry.type === "value_error" && field === "email") {
    return "올바른 이메일 형식이 아닙니다";
  }
  if (label && raw) return `${label}: ${raw}`;
  return raw || String(entry);
}

/** FastAPI `detail` (string | validation array) → 사용자 메시지 */
export function formatApiDetail(detail, fallback = "요청에 실패했습니다") {
  if (!detail) return fallback;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    return detail.map(validationEntryMessage).filter(Boolean).join(" ");
  }
  return fallback;
}
