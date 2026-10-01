Báo cáo:

## Kiến trúc
- Jenkins chạy trong container, dùng Docker socket & CLI của host để build/push.
- Pipeline: GitHub → Webhook → Jenkins → Build & Push Docker Hub → Deploy docker-compose trên EC2.
- Dịch vụ chạy: `thanhhuong29/dagster-user-code` (gRPC 3030), `victoriametrics/victoria-metrics` (8428/2003/4242), Jenkins (8080/50000).

## Các bước đã thực hiện
1) Jenkins/Ansible
   - Cài Jenkins, mount Docker socket/CLI, tắt setup wizard & CSRF để webhook hoạt động.
   - Cài plugin GitHub, bật trigger “GitHub hook trigger for GITScm polling”.
2) Jenkinsfile
   - Checkout từ GitHub.
   - Build image Dagster user code.
   - Login & Push Docker Hub: `thanhhuong29/dagster-user-code:latest`.
   - Deploy: `docker compose down && pull && up -d`.
3) docker-compose
   - Image user_code: `thanhhuong29/dagster-user-code:latest`.
   - Kèm `victoriametrics/victoria-metrics:latest`.
4) Webhook
   - URL: `http://44.193.2.117:8080/github-webhook/`.
   - Đã xanh; Jenkins tự build khi push.
   - Mở inbound SG port 8080 (0.0.0.0/0) để GitHub gọi được.
5) Kiểm thử
   - Push sửa README → Jenkins tự build/push/deploy thành công.
   - `docker ps` trên EC2: containers `dagster-user-code`, `victoriametrics`, `jenkins` đều Up.

## Trạng thái cuối
- CI/CD tự động hoạt động: Push code → Webhook → Jenkins build/push → Deploy docker-compose trên EC2.
- Hệ thống chạy ổn định với Dagster user code + VictoriaMetrics.

