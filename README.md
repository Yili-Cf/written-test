# 数据库实例管理系统 — 方案 A

基于 Python + Django + Celery 的企业内部数据库实例管理系统。


## 项目结构

```
django/
├── README.md                 # 方案文档
├── requirements.txt
├── manage.py
├── docker-compose.yml        # Redis 依赖
├── config/                   # Django 项目配置
│   ├── settings.py
│   ├── celery.py
│   ├── urls.py
│   └── wsgi.py
└── apps/
    └── inventory/            # 业务应用
        ├── models.py
        ├── serializers.py
        ├── views.py
        ├── urls.py
        ├── tasks.py
        ├── crypto.py         # 密码加解密
        ├── middleware.py     # 请求耗时中间件
        └── admin.py
```

---

## 数据模型设计

### Department（部门）

| 字段 | 类型 | 说明 |
|------|------|------|
| name | CharField(128) | 部门名称，唯一 |
| code | CharField(64) | 部门编码，唯一 |
| description | TextField | 描述，可空 |
| created_at / updated_at | DateTimeField | 时间戳 |

### Cluster（集群）

| 字段 | 类型 | 说明 |
|------|------|------|
| name | CharField(128) | 集群名称 |
| code | CharField(64) | 集群编码，唯一 |
| department | FK → Department | 所属部门 |
| env | CharField | 环境：dev/test/prod |
| description | TextField | 描述 |
| created_at / updated_at | DateTimeField | 时间戳 |

### DatabaseInstance（数据库实例）

| 字段 | 类型 | 说明 |
|------|------|------|
| name | CharField(128) | 实例名称 |
| host | CharField(255) | 主机地址 |
| port | PositiveIntegerField | 端口，默认 3306 |
| db_type | CharField | mysql/postgresql/redis/mongodb 等 |
| cluster | FK → Cluster | 所属集群 |
| status | CharField | running/stopped/unknown |
| username | CharField(128) | 管理账号用户名 |
| password_encrypted | TextField | Fernet 加密后的密码 |
| last_password_rotated_at | DateTimeField | 上次轮换时间，可空 |
| created_at / updated_at | DateTimeField | 时间戳 |

> 密码不以明文落库；读取时通过 `get_password()` / `set_password()` 加解密。

### InstanceDailyStat（每日统计）

| 字段 | 类型 | 说明 |
|------|------|------|
| stat_date | DateField | 统计日期 |
| department | FK → Department | 部门，可空（按集群汇总时也可填） |
| cluster | FK → Cluster | 集群，可空（按部门汇总时也可填） |
| dimension | CharField | `department` / `cluster` |
| instance_count | PositiveIntegerField | 实例数量 |
| created_at | DateTimeField | 写入时间 |

唯一约束：`(stat_date, dimension, department, cluster)`

---

## API 设计

Base URL: `/api/`

### 部门

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/departments/` | 列表 |
| POST | `/api/departments/` | 创建 |
| GET | `/api/departments/{id}/` | 详情 |
| PUT/PATCH | `/api/departments/{id}/` | 更新 |
| DELETE | `/api/departments/{id}/` | 删除 |

### 集群

| 方法 | 路径 | 说明 |
|------|------|------|
| GET/POST | `/api/clusters/` | 列表 / 创建 |
| GET/PUT/PATCH/DELETE | `/api/clusters/{id}/` | 详情 / 更新 / 删除 |

### 实例

| 方法 | 路径 | 说明 |
|------|------|------|
| GET/POST | `/api/instances/` | 列表 / 创建（创建时传明文 password，入库加密） |
| GET/PUT/PATCH/DELETE | `/api/instances/{id}/` | 详情 / 更新 / 删除 |
| POST | `/api/instances/{id}/probe/` | TCP 端口可达探测|


### 统计查询（可选只读）

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/stats/` | 查询每日统计|

---

## Celery 定时任务

| 任务 | 调度 | 说明 |
|------|------|------|
| `rotate_all_instance_passwords` | 每 12 小时 | 为每个实例生成随机密码，Fernet 加密写入，更新 `last_password_rotated_at` |
| `collect_daily_instance_stats` | 每天 00:00 | 按部门、按集群分别统计实例数，写入 `InstanceDailyStat` |

Broker：`redis://127.0.0.1:6379/0`

---

## 请求耗时中间件

`RequestTimingMiddleware`：

1. 请求进入时记录 `time.perf_counter()`
2. 响应返回前计算耗时（毫秒）
3. 写入响应头 `X-Request-Duration-Ms`
4. 使用 logging 输出：`method path status duration_ms`

---


## 本地运行步骤

```bash
# 1. 创建虚拟环境并安装依赖
python -m venv .venv
# Windows:
.venv\Scripts\activate
pip install -r requirements.txt

2. 配置环境变量
set FERNET_KEY=...   # 若不设，开发环境会自动生成并打印提示
set REDIS_URL=redis://127.0.0.1:6379/0

# 3. 迁移并启动
python manage.py migrate
python manage.py runserver

celery -A config worker -l info
celery -A config beat -l info
启动 Redis可用 `docker compose up -d redis`。