/** backend SignupIn 과 동일 규칙 */
const EMAIL_RE = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
const USERNAME_RE = /^[a-zA-Z0-9._]{1,30}$/;

export function normalizeSignupPayload(form) {
  return {
    email: form.email.trim().toLowerCase(),
    username: form.username.trim().toLowerCase(),
    full_name: (form.full_name || "").trim(),
    password: form.password,
  };
}

export function validateSignupPayload(payload) {
  if (!EMAIL_RE.test(payload.email)) {
    return "올바른 이메일 형식이 아닙니다 (예: name@gmail.com)";
  }
  if (!USERNAME_RE.test(payload.username)) {
    return "사용자 이름은 영문, 숫자, 밑줄(_), 마침표(.)만 1~30자까지 사용할 수 있습니다";
  }
  if (payload.password.length < 8) {
    return "비밀번호는 8자 이상이어야 합니다";
  }
  return "";
}
