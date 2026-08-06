# Contributing to CodeSandBox

Cảm ơn bạn đã quan tâm đóng góp cho CodeSandBox! Mục tiêu của tài liệu này là giúp việc đóng góp trở nên dễ hiểu, nhất quán và nhanh chóng — từ báo lỗi, đề xuất tính năng tới gửi Pull Request (PR).

## Mục lục
- Giới thiệu ngắn
- Bộ quy tắc chung
- Bắt đầu nhanh (setup)
- Luồng làm việc (branching & PR)
- Quy ước commit
- Viết PR chất lượng — checklist
- Viết issue (bug / feature)
- Kiểm tra & testing
- Linting & formatting
- Code review và merge
- Vấn đề bảo mật
- Liên hệ & kênh thảo luận

---

## Giới thiệu ngắn
CodeSandBox là một project TypeScript-first. Trước khi gửi thay đổi lớn, vui lòng mở issue để thảo luận ý tưởng nếu chưa có. Các đóng góp nhỏ (ghi chú, sửa lỗi cú pháp, docs) có thể gửi PR trực tiếp theo hướng dẫn bên dưới.

## Bộ quy tắc chung
- Tôn trọng, lịch sự và xây dựng trong mọi trao đổi.
- Viết mô tả rõ ràng cho issue và PR.
- Đảm bảo mọi commit và PR đều đi kèm test phù hợp nếu thay đổi logic.
- Tuân theo quy ước mã nguồn (TypeScript + ESLint + Prettier).

> Nếu dự án có CODE_OF_CONDUCT.md, vui lòng đọc và tuân thủ nó trước khi đóng góp.

## Bắt đầu nhanh (Setup)
Yêu cầu:
- Node.js LTS (khuyến nghị >= 18)
- Git
- npm / yarn / pnpm (chọn 1)

Ví dụ (npm):
```bash
git clone https://github.com/nvht2505-dot/CodeSandBox.git
cd CodeSandBox
npm install
npm run build        # (nếu cần)
npm run dev          # chạy môi trường dev nếu có
```

Nếu dùng nvm:
```bash
nvm use --lts
```

Thêm hướng dẫn môi trường (ENV) nếu repository cần biến môi trường — đặt file .env.example để tham khảo.

## Luồng làm việc (Branching & PR)
- Fork repository (nếu bạn không có quyền push).
- Tạo branch từ main: `git checkout -b feat/<mô-tả-ngắn>` hoặc `fix/<mô-tả-ngắn>`.
- Giữ branch nhỏ, focused và rebase/sync thường xuyên với nhánh chính.
- Khi hoàn tất, push và mở Pull Request vào nhánh chính (ví dụ `main`).

Tên branch gợi ý:
- feat/... (tính năng)
- fix/... (sửa lỗi)
- docs/... (tài liệu)
- chore/... (công việc không thay đổi logic)

## Quy ước commit
Chúng tôi dùng Conventional Commits để giữ lịch sử rõ ràng:
- feat: Thêm tính năng mới
- fix: Sửa lỗi
- docs: Tài liệu
- style: Định dạng, khoảng trắng, không thay đổi logic
- refactor: Sửa đổi code nhưng không thêm tính năng hay sửa lỗi
- test: Thêm/sửa test
- chore: Công việc build/ci/dep

Ví dụ:
```
git commit -m "feat(ui): add responsive toolbar for editor"
git commit -m "fix(api): handle null response from /preview"
```

## Viết PR chất lượng — Checklist
Trước khi request review, tự kiểm tra:
- [ ] PR có tiêu đề rõ ràng và mô tả đầy đủ: tóm tắt, lý do, cách kiểm thử.
- [ ] Đã liên kết tới issue (nếu có): `Fixes #123` hoặc `Closes #123`.
- [ ] Không có lỗi lint: `npm run lint` chạy qua.
- [ ] Tất cả test đều pass: `npm test`.
- [ ] Đã thêm/ cập nhật test cho logic mới.
- [ ] Không commit secrets / thông tin nhạy cảm.
- [ ] Kích thước diff nhỏ và có thể review dễ dàng.

Mẫu mô tả PR ngắn:
- Mô tả ngắn (1–2 câu)
- Thay đổi chính
- Cách test (steps)
- Checklist (lint, test, docs)

## Viết issue (bug / feature)
Khi mở issue, cung cấp:
- Tiêu đề rõ ràng.
- Môi trường (OS, Node version, trình duyệt nếu liên quan).
- Mô tả mong đợi vs thực tế.
- Các bước để tái hiện (repro steps).
- Log / stack trace / screenshot nếu có.
- Gắn label nếu bạn đề xuất (bug/feature/docs).

Feature request: mô tả use-case, lợi ích, UX flow hoặc đề xuất kỹ thuật nếu có.

## Kiểm tra & testing
- Chạy unit/integration tests: `npm test` hoặc `npm run test:watch`.
- Nếu thêm code mới, kèm theo test phù hợp.
- Chạy kiểm tra type: `npm run typecheck` (nếu có).
- CI sẽ thực thi test + lint trước khi merge.

## Linting & formatting
- ESLint + Prettier được khuyến nghị.
- Chạy:
```bash
npm run lint
npm run format
```
- Cấu hình dự án có thể tự động format trước commit bằng Husky/linters-staged. Nếu không, hãy format thủ công.

## Code review và merge
- PR sẽ được review bởi ít nhất một maintainer.
- Review focus: correctness, readability, testing, security, performance.
- Sau khi được approve và CI pass, maintainer sẽ merge.
- Sử dụng fast-forward/rebase hoặc squash-merge theo chính sách repo (nêu rõ policy nếu cần).

## Vấn đề bảo mật
Nếu bạn phát hiện lỗ hổng bảo mật, đừng public issue công khai. Vui lòng báo trực tiếp tới maintainer hoặc email bảo mật (nếu có) với chi tiết để xử lý riêng. Sau khi fix, maintainer sẽ công bố bản vá công khai.

## Tài nguyên & liên hệ
- Repo: https://github.com/nvht2505-dot/CodeSandBox
- Nếu cần trao đổi nhanh: mở issue với label `discussion` hoặc ping maintainer trong kênh giao tiếp của dự án (Slack/Discord nếu có).

---

Cảm ơn bạn đã đóng góp — mọi đóng góp, dù nhỏ, đều giúp CodeSandBox tốt hơn!
