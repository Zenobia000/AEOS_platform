# AEOS Observability Stack（Phase 1 IaC）

對應 [`docs/2-contracts/OBS-001-observability-spec.md`](../../docs/2-contracts/OBS-001-observability-spec.md) §10 W1 交付：**Prometheus + Grafana + Loki on Hetzner CX22**。

本目錄是 *infrastructure-as-code*：在 Hetzner 帳號開好後 `docker compose up -d` 即可上線。**目前狀態：可離線預覽 / 校驗，未實際部署**。

## 檔案結構

```
infra/observability/
├── docker-compose.yml              # Prometheus + Loki + Promtail + Grafana + node-exporter
├── .env.example                    # 需複製為 .env 後填密碼
├── prometheus/
│   ├── prometheus.yml              # scrape targets（host.docker.internal:8000 = AEOS API）
│   └── alerts.yml                  # 5 條起手規則（OBS-001 §7）
├── loki/
│   ├── loki-config.yml             # 30 天 hot retention（OBS-001 §1）
│   └── promtail-config.yml         # 抓 docker stdout JSON logs
├── grafana/
│   ├── provisioning/datasources/   # 自動接 Prometheus + Loki
│   ├── provisioning/dashboards/    # 自動載入 dashboards 目錄
│   └── dashboards/
│       ├── golden-signals.json     # OBS-001 §2 + §6 (RPS / 5xx / p95 latency / CPU / mem)
│       └── business-kpis.json      # OBS-001 §3 (auto-reply rate / pass rate / LLM cost / tokens)
└── nginx/aeos.conf                 # TLS terminator 範例（obs / api / expert 三個子域）
```

## 部署 runbook（待 Hetzner 帳號開好後執行）

### 1. 開 Hetzner Cloud server

```sh
# Hetzner Cloud Console → Add Server
# Image:     Ubuntu 24.04
# Type:      CX22 (2 vCPU / 4 GB / 40 GB SSD, €4.5/月)
# Location:  Helsinki (hel1) / Falkenstein (fsn1)
# SSH key:   上傳 CTO 的 public key
```

對應 [SAD-v0.1](../../docs/2-contracts/SAD-v0.1.md) Phase 1：customer-dedicated VM + Docker Compose。

### 2. 基本 hardening

```sh
# 以 ssh root@<IP> 登入
adduser aeos && usermod -aG sudo aeos
# 鎖 root login
sed -i 's/^PermitRootLogin.*/PermitRootLogin no/' /etc/ssh/sshd_config
systemctl reload ssh

ufw allow OpenSSH
ufw allow 80
ufw allow 443
ufw enable

apt update && apt install -y docker.io docker-compose-v2 git
```

### 3. 拉 repo + 啟 stack

```sh
sudo -u aeos bash
git clone git@github.com:Zenobia000/AEOS_platform.git ~/aeos
cd ~/aeos/infra/observability
cp .env.example .env
# 改 .env：GRAFANA_ADMIN_PASSWORD / GRAFANA_ROOT_URL
docker compose up -d
docker compose ps   # 五個 container 都 Up
```

### 4. 接 DNS + TLS

```sh
# Cloudflare DNS：A obs.example.com → <Hetzner IP>
#                 A api.example.com → <Hetzner IP>
#                 A expert.example.com → <Hetzner IP>

sudo apt install -y nginx certbot python3-certbot-nginx
sudo cp infra/observability/nginx/aeos.conf /etc/nginx/sites-available/
sudo ln -s /etc/nginx/sites-available/aeos.conf /etc/nginx/sites-enabled/
sudo certbot --nginx -d obs.example.com -d api.example.com -d expert.example.com
sudo systemctl reload nginx
```

### 5. 驗證

| 檢查 | 預期 |
| --- | --- |
| `curl http://localhost:9090/-/healthy` | `Prometheus is Healthy.` |
| `curl http://localhost:3100/ready` | `ready` |
| `https://obs.example.com` | Grafana login（用 .env 內 admin/密碼） |
| Grafana → Dashboards → AEOS → Golden Signals | 五個 panel 可開（資料空 OK） |
| Grafana → Explore → Loki → `{service="aeos-api"}` | 待 AEOS 部署後可看 logs |

## 連接 AEOS app（待 W1 後續任務）

AEOS API 目前 `/metrics` 只是 placeholder（見 [`app/main.py`](../../app/main.py)）。下一支 branch 接 `prometheus-fastapi-instrumentator`（FastAPI middleware）+ custom counter / histogram，自然會被本 stack 抓到。

對應 metric 命名（OBS-001 §3）：
- `aeos_conversations_total`
- `aeos_test_set_pass_rate`
- `aeos_e2e_latency_seconds`
- `aeos_llm_tokens_total`
- `aeos_llm_cost_usd_total`
- `aeos_kb_ingest_jobs_total`

dashboards/business-kpis.json 已預先以這些名稱寫好查詢。

## 維護

| 任務 | 頻率 |
| --- | --- |
| `docker compose pull && up -d` 升版 | 月 |
| Backup `prometheus-data / loki-data / grafana-data` volume | 週（RUNBOOK-003） |
| Cold log 搬 S3 | 月（Loki retention 30 天 hot） |
| Slack/PagerDuty 告警路由設定 | OBS-001 §7（待 oncall 帳號就緒） |

## 後續強化（Phase 2+）

- [ ] Tempo for distributed tracing（OBS-001 §5）
- [ ] Alertmanager 接 Slack/PagerDuty
- [ ] Loki S3 backend（cold tier，> 30 天）
- [ ] Grafana OnCall（替代 PagerDuty）
- [ ] mTLS for prometheus scrape across hosts（多 tenant VM）
