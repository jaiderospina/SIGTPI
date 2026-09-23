#!/usr/bin/env python3
"""
SIGTPI Master Seed Script
Crea esquemas, tablas y datos de prueba completos.
Run: docker compose run --rm auth-service python3 -m app.seed
"""
import asyncio, sys, uuid, random
from datetime import datetime, timezone, timedelta, date

sys.path.insert(0, "/app")

# ── Schema list ────────────────────────────────────────────────────────────────
SCHEMAS = ["auth","users","academic","tutoring","ti","sessions","documents",
           "evaluation","notif","pki","audit"]

# ── Fake avatar URLs (use ui-avatars, free & no auth) ─────────────────────────
def avatar(name: str) -> str:
    n = name.replace(" ", "+")
    return f"https://ui-avatars.com/api/?name={n}&size=128&background=1F3864&color=fff"

# ── Data pools ────────────────────────────────────────────────────────────────
AREAS = [
    "Ciberseguridad y Ciberdefensa",
    "Redes y Telecomunicaciones",
    "Ciencia de Datos e Inteligencia Artificial",
    "Ingeniería de Software",
    "Gestión de Sistemas de Información",
]

TUTORS_DATA = [
    {"name":"Dr. Carlos Mendoza Ríos",   "email":"cmendoza@sigtpi.edu.co",   "area":AREAS[0], "bio":"PhD en Seguridad Informática, 15 años de experiencia en protección de infraestructuras críticas."},
    {"name":"Dra. Lucia Vargas Pinto",   "email":"lvargas@sigtpi.edu.co",    "area":AREAS[1], "bio":"Doctora en Telecomunicaciones, experta en redes SDN y protocolo IPv6."},
    {"name":"Dr. Andrés Torres Mejía",   "email":"atorres@sigtpi.edu.co",    "area":AREAS[2], "bio":"PhD en Inteligencia Artificial, investigador principal en aprendizaje federado."},
    {"name":"Dra. María Castro Ruiz",    "email":"mcastro@sigtpi.edu.co",    "area":AREAS[3], "bio":"Doctora en Ingeniería de Software, especialista en arquitecturas de microservicios."},
    {"name":"Dr. Jorge Rojas Herrera",   "email":"jrojas@sigtpi.edu.co",     "area":AREAS[4], "bio":"PhD en Sistemas de Información, experto en gobierno de datos y COBIT."},
]

STUDENTS_DATA = [
    {"name":"Ana Sofía Bermúdez López",  "email":"abermudez@est.sigtpi.edu.co",  "area":AREAS[0]},
    {"name":"Carlos Esteban Mora Ruiz",  "email":"cmora@est.sigtpi.edu.co",      "area":AREAS[1]},
    {"name":"Diana Paola García Soto",   "email":"dgarcia@est.sigtpi.edu.co",    "area":AREAS[2]},
    {"name":"Felipe Andrés Niño Cruz",   "email":"fnino@est.sigtpi.edu.co",      "area":AREAS[3]},
    {"name":"Valentina Ríos Pedraza",    "email":"vrios@est.sigtpi.edu.co",      "area":AREAS[4]},
    {"name":"Sebastián Gómez Alvarado",  "email":"sgomez@est.sigtpi.edu.co",     "area":AREAS[0]},
    {"name":"Laura Milena Pérez Cano",   "email":"lperez@est.sigtpi.edu.co",     "area":AREAS[1]},
    {"name":"Mateo Alejandro Silva Ríos","email":"msilva@est.sigtpi.edu.co",     "area":AREAS[2]},
    {"name":"Isabella Moreno Cadena",    "email":"imoreno@est.sigtpi.edu.co",    "area":AREAS[3]},
    {"name":"Santiago Duarte Vargas",    "email":"sduarte@est.sigtpi.edu.co",    "area":AREAS[4]},
]

TI_TITLES = [
    "Detección de intrusiones en redes OT mediante machine learning federado",
    "Framework de seguridad Zero Trust para entornos de nube híbrida",
    "Modelo predictivo de ataques APT usando grafos de conocimiento",
    "Análisis de vulnerabilidades en protocolos IoT industriales",
    "Sistema de respuesta automática ante incidentes de ciberseguridad",
    "Arquitectura SDN para la mitigación de ataques DDoS en tiempo real",
    "Protocolo de comunicación segura para redes de sensores inalámbricos",
    "Optimización de QoS en redes 5G mediante aprendizaje por refuerzo",
    "Clasificación automática de malware usando redes neuronales convolucionales",
    "Plataforma de análisis de Big Data para inteligencia de amenazas",
    "Modelo de gobierno de datos para entidades públicas colombianas",
    "Sistema de detección de deepfakes en contenido multimedia",
    "Framework DevSecOps para el ciclo de vida seguro del software",
    "Arquitectura de microservicios resiliente con patrones de circuit breaker",
    "Plataforma de gestión de identidades descentralizada basada en blockchain",
    "Análisis forense automatizado de artefactos de memoria RAM",
    "Sistema de recomendación de controles de seguridad basado en MITRE ATT&CK",
    "Evaluación de riesgos en infraestructuras críticas con lógica difusa",
    "Modelo de madurez en ciberseguridad para PYMES colombianas",
    "Plataforma de ciberentrenamiento gamificada para analistas SOC",
]

MILESTONES_TEMPLATE = [
    ("Aprobación de Anteproyecto", "anteproject_approval", True,  10.0, 60),
    ("Primer Avance Semestral",    "semester_advance",     False, 15.0, 150),
    ("Borrador Final",             "final_draft",          True,  25.0, 270),
    ("Defensa Preliminar",         "preliminary_defense",  True,  20.0, 330),
    ("Defensa Final",              "final_defense",        True,  30.0, 420),
]

ADVANCES_POOL = [
    ("2024-1", "Se realizó revisión exhaustiva de literatura especializada. Se identificaron 45 fuentes primarias. Se definió el alcance metodológico del trabajo.", 20.0, "Acceso limitado a bases de datos especializadas.", "Solicitar acceso institucional a IEEE Xplore y ACM Digital Library."),
    ("2024-2", "Se implementó el prototipo inicial del sistema. Se realizaron pruebas de concepto exitosas con dataset público. Se documentaron los primeros resultados.", 45.0, "El dataset público presenta desbalance de clases.", "Aplicar técnicas de oversampling SMOTE para balancear las clases."),
    ("2025-1", "Se completó la fase de experimentación con datos reales. Se obtuvieron métricas de precisión del 94.3%. Se redactó el capítulo de resultados.", 70.0, None, "Continuar con la redacción del capítulo de conclusiones."),
]


async def main():
    from sqlalchemy import text, String, Boolean, DateTime, Float, Integer, Date, Text, UniqueConstraint, ForeignKey
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
    from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
    from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB

    from app.core.config import settings

    # ── Wait for PostgreSQL ────────────────────────────────────────────────────
    import os
    _pg_host = os.getenv("POSTGRES_HOST", "postgres")
    _pg_port = int(os.getenv("POSTGRES_PORT", "5432"))
    _pg_user = os.getenv("POSTGRES_USER", "sigtpi")
    _pg_pass = os.getenv("POSTGRES_PASSWORD", "sigtpi_dev")
    _pg_db   = os.getenv("POSTGRES_DB", "sigtpi")
    print(f"⏳ Conectando a PostgreSQL ({_pg_host}:{_pg_port}/{_pg_db})...")
    import asyncpg as _apg
    for _attempt in range(30):
        try:
            _c = await _apg.connect(host=_pg_host, port=_pg_port,
                user=_pg_user, password=_pg_pass, database=_pg_db)
            await _c.close()
            print(f"  ✓ PostgreSQL listo")
            break
        except Exception as _e:
            if _attempt == 29:
                print(f"  ✗ PostgreSQL no responde: {_e}")
                raise SystemExit(1)
            print(f"  · Intento {_attempt+1}/30, esperando 3s...")
            await asyncio.sleep(3)

    # Build DB URL directly from env vars — avoids any config class bugs
    import os as _os
    _pg_user = _os.getenv("POSTGRES_USER", "sigtpi")
    _pg_pass = _os.getenv("POSTGRES_PASSWORD", "sigtpi_dev")
    _pg_host = _os.getenv("POSTGRES_HOST", "postgres")
    _pg_port = _os.getenv("POSTGRES_PORT", "5432")
    _pg_db   = _os.getenv("POSTGRES_DB", "sigtpi")
    _db_url  = f"postgresql+asyncpg://{_pg_user}:{_pg_pass}@{_pg_host}:{_pg_port}/{_pg_db}"
    engine = create_async_engine(
        _db_url,
        echo=False,
        connect_args={"server_settings": {
            "search_path": "public,users,academic,tutoring,ti,sessions,evaluation,documents,notif,pki"
        }},
    )
    Session = async_sessionmaker(engine, expire_on_commit=False)

    # ── 1. Create schemas ──────────────────────────────────────────────────────
    async with engine.begin() as conn:
        for s in SCHEMAS:
            await conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {s}"))
    print(f"✓ Schemas: {', '.join(SCHEMAS)}")

    # ── 2. Define all models inline ────────────────────────────────────────────
    class Base(DeclarativeBase):
        pass

    # public.users (auth-service default schema)
    class AuthUser(Base):
        __tablename__ = "users"
        __table_args__ = {}
        id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
        email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
        hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
        full_name: Mapped[str] = mapped_column(String(255), nullable=False)
        is_active: Mapped[bool] = mapped_column(Boolean, default=True)
        is_superuser: Mapped[bool] = mapped_column(Boolean, default=False)
        totp_secret: Mapped[str | None] = mapped_column(String(64), nullable=True)
        totp_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
        failed_login_attempts: Mapped[int] = mapped_column(Integer, default=0)
        locked_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
        last_login: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
        created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
        updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    # users.users
    class UserProfile(Base):
        __tablename__ = "users"
        __table_args__ = {"schema": "users"}
        id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
        email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
        full_name: Mapped[str] = mapped_column(String(255), nullable=False)
        document_id: Mapped[str | None] = mapped_column(String(50), nullable=True)
        phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
        photo_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
        bio: Mapped[str | None] = mapped_column(Text, nullable=True)
        area_of_expertise: Mapped[str | None] = mapped_column(String(255), nullable=True)
        status: Mapped[str] = mapped_column(String(20), default="active")
        is_superuser: Mapped[bool] = mapped_column(Boolean, default=False)
        created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
        updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    # users.user_roles
    class UserRole(Base):
        __tablename__ = "user_roles"
        __table_args__ = (UniqueConstraint("user_id","role_code", name="uq_ur_seed"), {"schema":"users"})
        id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
        user_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
        role_code: Mapped[str] = mapped_column(String(10), nullable=False)
        program_id: Mapped[uuid.UUID | None] = mapped_column(PGUUID(as_uuid=True), nullable=True)
        is_active: Mapped[bool] = mapped_column(Boolean, default=True)
        assigned_by: Mapped[uuid.UUID | None] = mapped_column(PGUUID(as_uuid=True), nullable=True)
        assigned_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
        expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # academic.programs
    class Program(Base):
        __tablename__ = "programs"
        __table_args__ = {"schema": "academic"}
        id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
        code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
        name: Mapped[str] = mapped_column(String(255), nullable=False)
        level: Mapped[str] = mapped_column(String(50), nullable=False)
        duration_semesters: Mapped[int | None] = mapped_column(Integer, nullable=True, default=4)
        duration_months: Mapped[int | None] = mapped_column(Integer, nullable=True)
        max_students_per_tutor: Mapped[int] = mapped_column(Integer, default=5)
        min_gpa_for_ti: Mapped[float] = mapped_column(Float, default=3.5)
        description: Mapped[str | None] = mapped_column(Text, nullable=True)
        coordinator_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
        status: Mapped[str] = mapped_column(String(50), default="active")
        director_id: Mapped[uuid.UUID | None] = mapped_column(PGUUID(as_uuid=True), nullable=True)
        created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
        updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    # academic.enrollments
    class Enrollment(Base):
        __tablename__ = "enrollments"
        __table_args__ = {"schema": "academic"}
        id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
        student_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
        program_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
        cohort: Mapped[str] = mapped_column(String(20), nullable=False)
        status: Mapped[str] = mapped_column(String(20), default="active")
        enrollment_date: Mapped[date] = mapped_column(Date, nullable=False)
        expected_graduation: Mapped[date | None] = mapped_column(Date, nullable=True)
        actual_graduation: Mapped[date | None] = mapped_column(Date, nullable=True)
        gpa: Mapped[float] = mapped_column(Float, default=0.0)
        ti_approved: Mapped[bool] = mapped_column(Boolean, default=False)
        notes: Mapped[str | None] = mapped_column(Text, nullable=True)
        created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
        updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    # tutoring.tutor_assignments
    class TutorAssignment(Base):
        __tablename__ = "tutor_assignments"
        __table_args__ = {"schema": "tutoring"}
        id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
        student_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
        tutor_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
        program_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
        research_area: Mapped[str] = mapped_column(String(255), nullable=False)
        preliminary_title: Mapped[str | None] = mapped_column(String(512), nullable=True)
        status: Mapped[str] = mapped_column(String(20), default="active")
        rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
        assigned_by: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
        requested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
        responded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
        activated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
        closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
        notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # ti.research_works
    class ResearchWork(Base):
        __tablename__ = "research_works"
        __table_args__ = {"schema": "ti"}
        id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
        assignment_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), unique=True, nullable=False)
        student_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
        tutor_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
        program_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
        title: Mapped[str] = mapped_column(String(512), nullable=False)
        knowledge_area: Mapped[str] = mapped_column(String(100), nullable=False)
        problem_statement: Mapped[str | None] = mapped_column(Text, nullable=True)
        objectives: Mapped[str | None] = mapped_column(Text, nullable=True)
        methodology: Mapped[str | None] = mapped_column(Text, nullable=True)
        keywords: Mapped[list | None] = mapped_column(JSONB, nullable=True)
        status: Mapped[str] = mapped_column(String(30), default="in_progress")
        progress_percent: Mapped[float] = mapped_column(Float, default=0.0)
        start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
        estimated_defense: Mapped[date | None] = mapped_column(Date, nullable=True)
        actual_defense: Mapped[date | None] = mapped_column(Date, nullable=True)
        created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
        updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    # ti.milestones
    class Milestone(Base):
        __tablename__ = "milestones"
        __table_args__ = {"schema": "ti"}
        id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
        ti_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
        name: Mapped[str] = mapped_column(String(255), nullable=False)
        description: Mapped[str | None] = mapped_column(Text, nullable=True)
        milestone_type: Mapped[str] = mapped_column(String(40), nullable=False)
        status: Mapped[str] = mapped_column(String(20), default="pending")
        planned_date: Mapped[date] = mapped_column(Date, nullable=False)
        actual_date: Mapped[date | None] = mapped_column(Date, nullable=True)
        weight_percent: Mapped[float] = mapped_column(Float, default=10.0)
        is_critical: Mapped[bool] = mapped_column(Boolean, default=False)
        approved_by: Mapped[uuid.UUID | None] = mapped_column(PGUUID(as_uuid=True), nullable=True)
        approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
        rejection_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
        created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    # ti.progress_advances
    class ProgressAdvance(Base):
        __tablename__ = "progress_advances"
        __table_args__ = {"schema": "ti"}
        id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
        ti_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
        period: Mapped[str] = mapped_column(String(20), nullable=False)
        activities_done: Mapped[str] = mapped_column(Text, nullable=False)
        progress_percent: Mapped[float] = mapped_column(Float, nullable=False)
        obstacles: Mapped[str | None] = mapped_column(Text, nullable=True)
        action_plan: Mapped[str | None] = mapped_column(Text, nullable=True)
        registered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
        registered_by: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)

    # ti.delay_alerts
    class DelayAlert(Base):
        __tablename__ = "delay_alerts"
        __table_args__ = {"schema": "ti"}
        id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
        ti_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
        milestone_id: Mapped[uuid.UUID | None] = mapped_column(PGUUID(as_uuid=True), nullable=True)
        level: Mapped[str] = mapped_column(String(1), nullable=False)
        reason: Mapped[str] = mapped_column(Text, nullable=False)
        status: Mapped[str] = mapped_column(String(20), default="active")
        justification: Mapped[str | None] = mapped_column(Text, nullable=True)
        detected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
        resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # sessions.tutoring_sessions
    class TutoringSession(Base):
        __tablename__ = "tutoring_sessions"
        __table_args__ = {"schema": "sessions"}
        id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
        ti_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
        tutor_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
        student_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
        scheduled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
        duration_minutes: Mapped[int] = mapped_column(Integer, default=60)
        modality: Mapped[str] = mapped_column(String(20), nullable=False)
        status: Mapped[str] = mapped_column(String(20), default="completed")
        agenda: Mapped[str | None] = mapped_column(Text, nullable=True)
        meeting_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
        meeting_room_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
        cancellation_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
        cancelled_by: Mapped[uuid.UUID | None] = mapped_column(PGUUID(as_uuid=True), nullable=True)
        rescheduled_from: Mapped[uuid.UUID | None] = mapped_column(PGUUID(as_uuid=True), nullable=True)
        created_by: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
        created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
        updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    # notif.notifications
    class Notification(Base):
        __tablename__ = "notifications"
        __table_args__ = {"schema": "notif"}
        id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
        recipient_id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
        recipient_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
        subject: Mapped[str] = mapped_column(String(255), nullable=False)
        body: Mapped[str] = mapped_column(Text, nullable=False)
        html_body: Mapped[str | None] = mapped_column(Text, nullable=True)
        channel: Mapped[str] = mapped_column(String(20), default="platform")
        priority: Mapped[str] = mapped_column(String(20), default="medium")
        status: Mapped[str] = mapped_column(String(20), default="sent")
        event_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
        reference_id: Mapped[uuid.UUID | None] = mapped_column(PGUUID(as_uuid=True), nullable=True)
        extra_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
        is_read: Mapped[bool] = mapped_column(Boolean, default=False)
        sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
        read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
        error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
        created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    # ── 3. Create all tables ────────────────────────────────────────────────────
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✓ All tables created")

    # ── 4. Seed data ────────────────────────────────────────────────────────────
    import bcrypt as _bcrypt
    now = datetime.now(timezone.utc)

    def make_hash(pw: str) -> str:
        return _bcrypt.hashpw(pw.encode(), _bcrypt.gensalt(rounds=10)).decode()

    async with Session() as db:

        # ── Admin ──────────────────────────────────────────────────────────────
        admin_id = uuid.uuid4()
        # ── Idempotency: skip if data already exists ──────────────────────────────
        existing = await db.execute(
            text("SELECT 1 FROM users WHERE email = 'admin@sigtpi.edu.co' LIMIT 1")
        )
        if existing.fetchone():
            print("  ℹ️  Datos de prueba ya existen — ejecuta 'docker compose down -v' para reiniciar.")
            return
        print("  ✓ Base de datos vacía — insertando datos...")

        db.add(AuthUser(id=admin_id, email="admin@sigtpi.edu.co",
            hashed_password=make_hash("Admin1234!@"), full_name="Administrador SIGTPI",
            is_active=True, is_superuser=True, failed_login_attempts=0,
            created_at=now, updated_at=now))
        db.add(UserProfile(id=admin_id, email="admin@sigtpi.edu.co",
            full_name="Administrador SIGTPI", status="active", is_superuser=True,
            area_of_expertise="Administración de Sistemas",
            bio="Administrador principal del Sistema de Gestión de Tutorías de Postgrado.",
            photo_url=avatar("Admin SIGTPI"),
            created_at=now, updated_at=now))
        db.add(UserRole(user_id=admin_id, role_code="ADM", is_active=True, assigned_at=now))
        print("  ✓ Admin user")

        # ── Coordinador ────────────────────────────────────────────────────────
        coo_id = uuid.uuid4()
        db.add(AuthUser(id=coo_id, email="coordinacion@sigtpi.edu.co",
            hashed_password=make_hash("Coord1234!@"), full_name="Coordinación Académica",
            is_active=True, is_superuser=False, failed_login_attempts=0,
            created_at=now, updated_at=now))
        db.add(UserProfile(id=coo_id, email="coordinacion@sigtpi.edu.co",
            full_name="Coordinación Académica", status="active",
            area_of_expertise="Coordinación de Postgrados",
            bio="Coordinadora del proceso tutorial de los programas de Maestría y Doctorado.",
            photo_url=avatar("Coordinacion"), created_at=now, updated_at=now))
        db.add(UserRole(user_id=coo_id, role_code="COO", is_active=True, assigned_at=now, assigned_by=admin_id))
        print("  ✓ Coordinator")

        # ── Director ────────────────────────────────────────────────────────────
        dir_id = uuid.uuid4()
        db.add(AuthUser(id=dir_id, email="direccion@sigtpi.edu.co",
            hashed_password=make_hash("Direct1234!@"), full_name="Dirección de Programas",
            is_active=True, is_superuser=False, failed_login_attempts=0,
            created_at=now, updated_at=now))
        db.add(UserProfile(id=dir_id, email="direccion@sigtpi.edu.co",
            full_name="Dirección de Programas", status="active",
            area_of_expertise="Dirección Académica",
            bio="Director de los programas de posgrado en Tecnología. PhD en Educación Superior.",
            photo_url=avatar("Direccion"), created_at=now, updated_at=now))
        db.add(UserRole(user_id=dir_id, role_code="DIR", is_active=True, assigned_at=now, assigned_by=admin_id))
        print("  ✓ Director")

        await db.flush()

        # ── Programs ────────────────────────────────────────────────────────────
        prog1_id = uuid.uuid4()
        prog2_id = uuid.uuid4()

        db.add(Program(id=prog1_id, code="MCDS", name="Maestría en Ciberseguridad y Ciberdefensa",
            level="maestria", duration_semesters=4, max_students_per_tutor=5, min_gpa_for_ti=3.5,
            description="Programa de maestría enfocado en seguridad de sistemas, análisis de vulnerabilidades y ciberdefensa nacional.",
            status="active", director_id=dir_id, created_at=now, updated_at=now))

        db.add(Program(id=prog2_id, code="MCIA",
            name="Maestría en Ciencia de Datos e Inteligencia Artificial",
            level="maestria", duration_semesters=4, max_students_per_tutor=5, min_gpa_for_ti=3.5,
            description="Programa de maestría en análisis de datos masivos, aprendizaje automático y sistemas de IA aplicada.",
            status="active", director_id=dir_id, created_at=now, updated_at=now))
        await db.flush()
        print("  ✓ 2 programs")

        # ── Tutors ─────────────────────────────────────────────────────────────
        tutor_ids = []
        for i, t in enumerate(TUTORS_DATA):
            tid = uuid.uuid4()
            tutor_ids.append(tid)
            db.add(AuthUser(id=tid, email=t["email"],
                hashed_password=make_hash("Tutor1234!@"), full_name=t["name"],
                is_active=True, is_superuser=False, failed_login_attempts=0,
                created_at=now, updated_at=now))
            db.add(UserProfile(id=tid, email=t["email"], full_name=t["name"],
                status="active", area_of_expertise=t["area"], bio=t["bio"],
                photo_url=avatar(t["name"]),
                phone=f"310{i+1:07d}", document_id=f"10{i+1:08d}",
                created_at=now, updated_at=now))
            prog_id = prog1_id if i < 3 else prog2_id
            db.add(UserRole(user_id=tid, role_code="TUT", program_id=prog_id,
                is_active=True, assigned_at=now, assigned_by=admin_id))
        await db.flush()
        print(f"  ✓ {len(tutor_ids)} tutors")

        # ── Students ────────────────────────────────────────────────────────────
        student_ids = []
        for i, s in enumerate(STUDENTS_DATA):
            sid = uuid.uuid4()
            student_ids.append(sid)
            prog_id = prog1_id if i < 5 else prog2_id
            db.add(AuthUser(id=sid, email=s["email"],
                hashed_password=make_hash("Est1234!@"), full_name=s["name"],
                is_active=True, is_superuser=False, failed_login_attempts=0,
                created_at=now, updated_at=now))
            db.add(UserProfile(id=sid, email=s["email"], full_name=s["name"],
                status="active", area_of_expertise=s["area"],
                bio=f"Estudiante de maestría en {s['area']}. Investigador en formación con interés en aplicaciones avanzadas del área.",
                photo_url=avatar(s["name"]),
                phone=f"311{i+1:07d}", document_id=f"10{20+i+1:08d}",
                created_at=now, updated_at=now))
            db.add(UserRole(user_id=sid, role_code="EST", program_id=prog_id,
                is_active=True, assigned_at=now, assigned_by=admin_id))
            enroll_date = date(2024, 1, 15)
            gpa_val = round(random.uniform(3.5, 4.8), 2)
            db.add(Enrollment(id=uuid.uuid4(), student_id=sid, program_id=prog_id,
                cohort="2024-1", status="active", enrollment_date=enroll_date,
                expected_graduation=date(2025, 11, 30),
                gpa=gpa_val, ti_approved=False, created_at=now, updated_at=now))
        await db.flush()
        print(f"  ✓ {len(student_ids)} students")

        # ── Assignments + TIs + Milestones + Advances ─────────────────────────
        ti_count = 0
        for i in range(20):
            student_id = student_ids[i % len(student_ids)]
            tutor_id   = tutor_ids[i % len(tutor_ids)]
            prog_id    = prog1_id if i < 10 else prog2_id

            # Tutor assignment
            asgn_id = uuid.uuid4()
            days_ago = random.randint(180, 400)
            asgn_date = now - timedelta(days=days_ago)
            db.add(TutorAssignment(id=asgn_id,
                student_id=student_id, tutor_id=tutor_id, program_id=prog_id,
                research_area=AREAS[i % len(AREAS)],
                preliminary_title=TI_TITLES[i],
                status="active", assigned_by=coo_id,
                requested_at=asgn_date, responded_at=asgn_date + timedelta(days=2),
                activated_at=asgn_date + timedelta(days=2)))

            # Progress level based on index
            if i < 4:
                prog_level, ti_status, n_advances = 70.0, "in_progress", 3
            elif i < 8:
                prog_level, ti_status, n_advances = 45.0, "in_progress", 2
            elif i < 14:
                prog_level, ti_status, n_advances = 20.0, "anteproject", 1
            else:
                prog_level, ti_status, n_advances = 10.0, "draft", 0

            start = asgn_date.date()
            ti_id = uuid.uuid4()
            db.add(ResearchWork(id=ti_id, assignment_id=asgn_id,
                student_id=student_id, tutor_id=tutor_id, program_id=prog_id,
                title=TI_TITLES[i], knowledge_area=AREAS[i % len(AREAS)],
                problem_statement=f"La investigación aborda el problema de {TI_TITLES[i].lower()} en el contexto colombiano.",
                objectives=f"Desarrollar y validar un sistema para {TI_TITLES[i].lower()}.",
                methodology="Investigación aplicada con enfoque cuantitativo. Diseño experimental con grupos de control.",
                keywords=[AREAS[i % len(AREAS)], "investigación", "postgrado"],
                status=ti_status, progress_percent=prog_level,
                start_date=start,
                estimated_defense=(start + timedelta(days=548)),
                created_at=asgn_date, updated_at=now))
            await db.flush()

            # Milestones
            for j, (mname, mtype, critical, weight, offset_days) in enumerate(MILESTONES_TEMPLATE):
                planned = start + timedelta(days=offset_days)
                m_status = "pending"
                actual = None
                approved_by = None
                approved_at = None

                if prog_level >= 70 and j <= 2:
                    m_status = "approved"
                    actual = planned - timedelta(days=random.randint(0, 10))
                    approved_by = tutor_id
                    approved_at = asgn_date + timedelta(days=offset_days + 5)
                elif prog_level >= 45 and j <= 1:
                    m_status = "approved"
                    actual = planned
                    approved_by = tutor_id
                    approved_at = asgn_date + timedelta(days=offset_days + 3)
                elif prog_level >= 20 and j == 0:
                    m_status = "approved"
                    actual = planned
                    approved_by = tutor_id
                    approved_at = asgn_date + timedelta(days=offset_days + 7)

                db.add(Milestone(id=uuid.uuid4(), ti_id=ti_id,
                    name=mname, milestone_type=mtype, status=m_status,
                    planned_date=planned, actual_date=actual,
                    weight_percent=weight, is_critical=critical,
                    approved_by=approved_by, approved_at=approved_at,
                    created_at=asgn_date))

            # Advances
            for k in range(n_advances):
                period, acts, pct, obs, plan = ADVANCES_POOL[k]
                db.add(ProgressAdvance(id=uuid.uuid4(), ti_id=ti_id,
                    period=period, activities_done=acts,
                    progress_percent=pct, obstacles=obs, action_plan=plan,
                    registered_at=asgn_date + timedelta(days=60*(k+1)),
                    registered_by=student_id))

            # Alert for delayed TIs
            if i >= 14:
                db.add(DelayAlert(id=uuid.uuid4(), ti_id=ti_id,
                    level="2", reason="TI con más de 60 días sin registrar avances.",
                    status="active", detected_at=now - timedelta(days=15)))

            # Sessions (2-4 per TI)
            n_sessions = random.randint(2, 4)
            for s in range(n_sessions):
                s_date = asgn_date + timedelta(days=30*(s+1))
                room_id = f"sigtpi-{str(ti_id)[:8]}-{s}"
                modality = "virtual" if s % 2 == 0 else "presential"
                db.add(TutoringSession(id=uuid.uuid4(),
                    ti_id=ti_id, tutor_id=tutor_id, student_id=student_id,
                    scheduled_at=s_date, duration_minutes=60,
                    modality=modality, status="completed",
                    agenda=f"Revisión de avance #{s+1}: metodología y resultados parciales.",
                    meeting_url=f"https://meet.sigtpi.local/{room_id}" if modality=="virtual" else None,
                    meeting_room_id=room_id if modality=="virtual" else None,
                    created_by=tutor_id, created_at=s_date, updated_at=s_date))

            ti_count += 1

        await db.flush()
        print(f"  ✓ {ti_count} TIs with milestones, advances and sessions")

        # ── Notifications for admin ────────────────────────────────────────────
        notifs = [
            ("Sistema inicializado", "El SIGTPI v2.0 ha sido configurado correctamente con datos de prueba.", "medium", "system.init"),
            ("6 TIs con alertas de retraso", "Existen TIs que requieren atención inmediata del coordinador.", "high", "ti.delay.alert"),
            ("10 estudiantes matriculados", "Se han registrado 10 estudiantes en los programas activos.", "low", "enrollment.created"),
            ("5 tutores disponibles", "Los tutores han sido asignados a sus programas correspondientes.", "medium", "tutor.assigned"),
        ]
        for subj, body, prio, evt in notifs:
            db.add(Notification(id=uuid.uuid4(), recipient_id=admin_id,
                recipient_email="admin@sigtpi.edu.co", subject=subj, body=body,
                channel="platform", priority=prio, status="sent", event_type=evt,
                is_read=False, sent_at=now, created_at=now))

        await db.commit()
        print("  ✓ Notifications")

    await engine.dispose()

    print()
    print("═══════════════════════════════════════════════════════")
    print("✅  SIGTPI — Datos de prueba cargados exitosamente")
    print("───────────────────────────────────────────────────────")
    print("  URL:           http://localhost:3000")
    print()
    print("  👤 ADMINISTRADOR")
    print("     admin@sigtpi.edu.co         / Admin1234!@")
    print()
    print("  👤 COORDINADOR")
    print("     coordinacion@sigtpi.edu.co  / Coord1234!@")
    print()
    print("  👤 DIRECTOR")
    print("     direccion@sigtpi.edu.co     / Direct1234!@")
    print()
    print("  👤 TUTORES (5)")
    print("     cmendoza@sigtpi.edu.co      / Tutor1234!@")
    print("     lvargas@sigtpi.edu.co       / Tutor1234!@")
    print("     atorres@sigtpi.edu.co       / Tutor1234!@")
    print()
    print("  👤 ESTUDIANTES (10)")
    print("     abermudez@est.sigtpi.edu.co / Est1234!@")
    print("     cmora@est.sigtpi.edu.co     / Est1234!@")
    print("     (todos con misma contraseña)")
    print()
    print("  📊 DATOS CARGADOS")
    print("     2 programas de maestría")
    print("     3 usuarios administrativos (ADM, COO, DIR)")
    print("     5 tutores con perfil completo")
    print("     10 estudiantes con perfil completo")
    print("     20 TIs con hitos, avances y sesiones")
    print("     6 alertas de retraso activas")
    print("     4 notificaciones al administrador")
    print("═══════════════════════════════════════════════════════")


if __name__ == "__main__":
    asyncio.run(main())
