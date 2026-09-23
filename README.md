# SIGTPI v2.0

**Sistema Integral de Gestión de Tutorías de Postgrado y Trabajos de Investigación**

Plataforma web autónoma (sin dependencias externas) para la gestión del proceso tutorial en programas de maestría y doctorado.

## Arquitectura

12 microservicios Python/FastAPI orquestados con Docker Compose.  
Infraestructura 100% self-hosted: PostgreSQL, Redis, RabbitMQ, Jitsi, Postal SMTP, PKI interno.

## Inicio rápido

```bash
# 1. Clonar y configurar
git clone <repo-url> sigtpi && cd sigtpi
cp .env.example .env          # revisar y ajustar valores

# 2. Levantar todo el stack
make up

# 3. Verificar que todo corra
make health
```

### URLs de desarrollo

| Servicio            | URL                        | Notas                    |
|---------------------|----------------------------|--------------------------|
| API Gateway         | http://localhost:8080       | Punto de entrada único   |
| auth-service docs   | http://localhost:8001/docs  | Swagger UI               |
| user-service docs   | http://localhost:8002/docs  |                          |
| ti-management docs  | http://localhost:8005/docs  |                          |
| RabbitMQ UI         | http://localhost:15672      | sigtpi / sigtpi_dev      |
| MailHog (email dev) | http://localhost:8025       | Captura todos los correos|
| Grafana             | http://localhost:3001       | admin / sigtpi_dev       |

## Estructura del proyecto

```
sigtpi/
├── services/                  # 12 microservicios FastAPI
│   ├── auth-service/          # Autenticación, JWT, MFA/TOTP   ← SPRINT 1 IMPL.
│   ├── user-service/          # Directorio de usuarios, RBAC
│   ├── academic-registry/     # Programas, cohortes, notas
│   ├── tutoring-service/      # Asignación de tutores
│   ├── ti-management/         # TI, cronogramas, alertas
│   ├── session-service/       # Sesiones, actas, WebRTC
│   ├── evaluation-service/    # Rúbricas, dictámenes
│   ├── document-service/      # Repositorio, PDF/A
│   ├── similarity-service/    # Motor TF-IDF
│   ├── notification-service/  # Cola de notificaciones
│   ├── report-service/        # Reportes, KPIs
│   └── pki-service/           # CA interna, X.509
├── shared/
│   └── sigtpi_common/         # Librería compartida (settings, JWT, ORM base, eventos)
├── infra/
│   ├── postgres/              # init.sql con schemas por servicio
│   ├── nginx/                 # API Gateway config
│   ├── rabbitmq/              # Exchange, queues, bindings
│   ├── prometheus/            # Scrape config
│   └── grafana/               # Dashboards
├── frontend/                  # React SPA (Sprint 3+)
├── .github/workflows/         # CI/CD
├── docker-compose.yml
├── Makefile
└── .env.example
```

## Comandos de desarrollo

```bash
make up            # Levanta todo el stack
make down          # Detiene todo
make logs          # Logs en tiempo real
make test          # Tests de todos los servicios
make test-svc SVC=auth-service   # Tests de un servicio
make migrate SVC=auth-service    # Migraciones Alembic
make shell SVC=auth-service      # Shell dentro del contenedor
make lint          # Lint con ruff
make health        # Verifica /health de todos los servicios
```

## Plan de sprints

| Sprint | Semanas | Entregable                                      |
|--------|---------|-------------------------------------------------|
| 1      | 1-2     | auth-service + user-service (✅ esqueleto listo) |
| 2      | 3-4     | academic-registry + tutoring-service            |
| 3      | 5-6     | ti-management + session-service                 |
| 4      | 7-8     | evaluation-service + pki-service                |
| 5      | 9-10    | document-service + similarity-service           |
| 6      | 11-12   | notification-service + report-service + frontend|

## Documentación de diseño

- `docs/srs/SIGTPI_SRS_v2.0_Autonomo.docx` — Requerimientos completos (IEEE 830)
- `docs/architecture/SIGTPI_Anexo_A_Arquitectura.docx` — Diagrama arquitectural
- `docs/deployment/SIGTPI_Anexo_B_Despliegue.docx` — Diagrama de despliegue
# SIGTPI
