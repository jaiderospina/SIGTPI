"""
SIGTPI — Database initialization script.

Replaces docker compose run --rm auth-service python3 -m app.seed

Handles both FRESH installs and UPGRADES:
- Creates schemas if missing
- Creates tables if missing (CREATE TABLE IF NOT EXISTS)
- Adds columns if missing (ALTER TABLE ADD COLUMN IF NOT EXISTS)
- Inserts seed data only if the users table is empty

Usage:
    docker compose run --rm auth-service python3 -m app.init_db
"""
import asyncio, os, uuid, secrets
from datetime import datetime, timezone

import asyncpg
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy import (
    String, Boolean, DateTime, Integer, Float, Text,
    ForeignKey, UniqueConstraint, JSON, Numeric
)


# ── Config ──────────────────────────────────────────────────────────────────
PG_HOST = os.getenv("POSTGRES_HOST", "postgres")
PG_PORT = int(os.getenv("POSTGRES_PORT", "5432"))
PG_USER = os.getenv("POSTGRES_USER", "sigtpi")
PG_PASS = os.getenv("POSTGRES_PASSWORD", "sigtpi_dev")
PG_DB   = os.getenv("POSTGRES_DB", "sigtpi")
DB_URL  = f"postgresql+asyncpg://{PG_USER}:{PG_PASS}@{PG_HOST}:{PG_PORT}/{PG_DB}"

SEARCH_PATH = "public,users,academic,tutoring,ti,sessions,evaluation,documents,notif,pki"
CONNECT_ARGS = {"server_settings": {"search_path": SEARCH_PATH}}

SCHEMAS = [
    "auth", "users", "academic", "tutoring", "ti", "sessions",
    "documents", "evaluation", "notif", "pki", "audit"
]


# ── Wait for postgres ────────────────────────────────────────────────────────
async def wait_for_postgres():
    print(f"⏳ Connecting to PostgreSQL ({PG_HOST}:{PG_PORT}/{PG_DB})...")
    for attempt in range(30):
        try:
            conn = await asyncpg.connect(
                host=PG_HOST, port=PG_PORT, user=PG_USER,
                password=PG_PASS, database=PG_DB
            )
            await conn.close()
            print(f"  ✓ PostgreSQL ready")
            return
        except Exception as e:
            if attempt == 29:
                raise SystemExit(f"  ✗ PostgreSQL not ready: {e}")
            print(f"  · Attempt {attempt+1}/30 — waiting 3s...")
            await asyncio.sleep(3)


# ── Migrations: add missing columns ─────────────────────────────────────────
COLUMN_MIGRATIONS = [
    # (schema, table, column, definition)
    ("academic", "programs", "coordinator_email", "VARCHAR(255)"),
    ("academic", "programs", "duration_months",   "INTEGER"),
    ("users",    "users",    "bio",               "TEXT"),
    ("users",    "users",    "photo_url",         "VARCHAR(500)"),
    ("users",    "users",    "document_id",       "VARCHAR(50)"),
    ("users",    "users",    "phone",             "VARCHAR(20)"),
    ("users",    "users",    "area_of_expertise", "VARCHAR(255)"),
    ("users",    "users",    "is_superuser",      "BOOLEAN DEFAULT FALSE"),
    ("users",    "user_roles", "expires_at",      "TIMESTAMP WITH TIME ZONE"),
    ("users",    "user_roles", "assigned_at",     "TIMESTAMP WITH TIME ZONE DEFAULT NOW()"),
    ("users",    "user_roles", "assigned_by",     "UUID"),
]

async def run_migrations(conn):
    """Add missing columns to existing tables (safe to run multiple times)."""
    print("🔧 Running column migrations...")
    for schema, table, column, definition in COLUMN_MIGRATIONS:
        try:
            await conn.execute(f"""
                ALTER TABLE {schema}.{table}
                ADD COLUMN IF NOT EXISTS {column} {definition}
            """)
            print(f"  ✓ {schema}.{table}.{column}")
        except Exception as e:
            print(f"  · {schema}.{table}.{column}: {e}")


# ── ORM models for table creation ───────────────────────────────────────────
class Base(DeclarativeBase):
    pass

class AuthUser(Base):
    __tablename__ = "users"
    __table_args__ = {}
    id:                    Mapped[uuid.UUID]       = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email:                 Mapped[str]             = mapped_column(String(255), unique=True, nullable=False)
    hashed_password:       Mapped[str]             = mapped_column(String(255), nullable=False)
    full_name:             Mapped[str]             = mapped_column(String(255), nullable=False)
    is_active:             Mapped[bool]            = mapped_column(Boolean, default=True)
    is_superuser:          Mapped[bool]            = mapped_column(Boolean, default=False)
    totp_secret:           Mapped[str | None]      = mapped_column(String(64), nullable=True)
    totp_enabled:          Mapped[bool]            = mapped_column(Boolean, default=False)
    failed_login_attempts: Mapped[int]             = mapped_column(Integer, default=0)
    locked_until:          Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_login:            Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at:            Mapped[datetime]        = mapped_column(DateTime(timezone=True))
    updated_at:            Mapped[datetime]        = mapped_column(DateTime(timezone=True))

class UserProfile(Base):
    __tablename__ = "users"
    __table_args__ = {"schema": "users"}
    id:                    Mapped[uuid.UUID]  = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    email:                 Mapped[str]        = mapped_column(String(255), unique=True, nullable=False)
    full_name:             Mapped[str]        = mapped_column(String(255), nullable=False)
    document_id:           Mapped[str | None] = mapped_column(String(50), nullable=True)
    phone:                 Mapped[str | None] = mapped_column(String(20), nullable=True)
    photo_url:             Mapped[str | None] = mapped_column(String(500), nullable=True)
    bio:                   Mapped[str | None] = mapped_column(Text, nullable=True)
    area_of_expertise:     Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_superuser:          Mapped[bool]       = mapped_column(Boolean, default=False)
    status:                Mapped[str]        = mapped_column(String(50), default="active")
    created_at:            Mapped[datetime]   = mapped_column(DateTime(timezone=True))
    updated_at:            Mapped[datetime]   = mapped_column(DateTime(timezone=True))

class UserRole(Base):
    __tablename__ = "user_roles"
    __table_args__ = (UniqueConstraint("user_id", "role_code", name="uq_user_roles"), {"schema": "users"})
    id:          Mapped[uuid.UUID]       = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id:     Mapped[uuid.UUID]       = mapped_column(PGUUID(as_uuid=True), nullable=False)
    role_code:   Mapped[str]             = mapped_column(String(10), nullable=False)
    program_id:  Mapped[uuid.UUID | None]= mapped_column(PGUUID(as_uuid=True), nullable=True)
    is_active:   Mapped[bool]            = mapped_column(Boolean, default=True)
    assigned_by: Mapped[uuid.UUID | None]= mapped_column(PGUUID(as_uuid=True), nullable=True)
    assigned_at: Mapped[datetime]        = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    expires_at:  Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

class Program(Base):
    __tablename__ = "programs"
    __table_args__ = {"schema": "academic"}
    id:                    Mapped[uuid.UUID]  = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code:                  Mapped[str]        = mapped_column(String(20), unique=True, nullable=False)
    name:                  Mapped[str]        = mapped_column(String(255), nullable=False)
    level:                 Mapped[str]        = mapped_column(String(50), nullable=False)
    duration_semesters:    Mapped[int | None] = mapped_column(Integer, nullable=True, default=4)
    duration_months:       Mapped[int | None] = mapped_column(Integer, nullable=True)
    max_students_per_tutor:Mapped[int]        = mapped_column(Integer, default=5)
    min_gpa_for_ti:        Mapped[float]      = mapped_column(Float, default=3.5)
    description:           Mapped[str | None] = mapped_column(Text, nullable=True)
    coordinator_email:     Mapped[str | None] = mapped_column(String(255), nullable=True)
    status:                Mapped[str]        = mapped_column(String(50), default="active")
    director_id:           Mapped[uuid.UUID | None] = mapped_column(PGUUID(as_uuid=True), nullable=True)
    created_at:            Mapped[datetime]   = mapped_column(DateTime(timezone=True))
    updated_at:            Mapped[datetime]   = mapped_column(DateTime(timezone=True))

class Enrollment(Base):
    __tablename__ = "enrollments"
    __table_args__ = {"schema": "academic"}
    id:           Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id:   Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    program_id:   Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    status:       Mapped[str]       = mapped_column(String(50), default="active")
    enrolled_at:  Mapped[datetime]  = mapped_column(DateTime(timezone=True))

class SemesterGrade(Base):
    __tablename__ = "semester_grades"
    __table_args__ = {"schema": "academic"}
    id:            Mapped[uuid.UUID]       = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    enrollment_id: Mapped[uuid.UUID]       = mapped_column(PGUUID(as_uuid=True), nullable=False)
    semester:      Mapped[int]             = mapped_column(Integer, nullable=False)
    grade:         Mapped[float | None]    = mapped_column(Float, nullable=True)
    tutor_id:      Mapped[uuid.UUID | None]= mapped_column(PGUUID(as_uuid=True), nullable=True)
    status:        Mapped[str]             = mapped_column(String(50), default="draft")
    comments:      Mapped[str | None]      = mapped_column(Text, nullable=True)
    recorded_at:   Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

class SessionMinutes(Base):
    __tablename__ = "session_minutes"
    __table_args__ = {"schema": "sessions"}
    id:                   Mapped[uuid.UUID]       = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id:           Mapped[uuid.UUID]       = mapped_column(PGUUID(as_uuid=True), nullable=False)
    topics_covered:       Mapped[str | None]      = mapped_column(Text, nullable=True)
    agreements:           Mapped[str | None]      = mapped_column(Text, nullable=True)
    tutor_observations:   Mapped[str | None]      = mapped_column(Text, nullable=True)
    student_observations: Mapped[str | None]      = mapped_column(Text, nullable=True)
    status:               Mapped[str]             = mapped_column(String(50), default="pending")
    registered_at:        Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

class TutorAssignment(Base):
    __tablename__ = "tutor_assignments"
    __table_args__ = {"schema": "tutoring"}
    id:          Mapped[uuid.UUID]       = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id:  Mapped[uuid.UUID]       = mapped_column(PGUUID(as_uuid=True), nullable=False)
    tutor_id:    Mapped[uuid.UUID]       = mapped_column(PGUUID(as_uuid=True), nullable=False)
    program_id:  Mapped[uuid.UUID]       = mapped_column(PGUUID(as_uuid=True), nullable=False)
    status:      Mapped[str]             = mapped_column(String(50), default="pending")
    area:        Mapped[str | None]      = mapped_column(String(255), nullable=True)
    title:       Mapped[str | None]      = mapped_column(String(500), nullable=True)
    notes:       Mapped[str | None]      = mapped_column(Text, nullable=True)
    assigned_by: Mapped[uuid.UUID | None]= mapped_column(PGUUID(as_uuid=True), nullable=True)
    created_at:  Mapped[datetime]        = mapped_column(DateTime(timezone=True))
    updated_at:  Mapped[datetime]        = mapped_column(DateTime(timezone=True))

class ResearchWork(Base):
    __tablename__ = "research_works"
    __table_args__ = {"schema": "ti"}
    id:                     Mapped[uuid.UUID]  = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id:             Mapped[uuid.UUID]  = mapped_column(PGUUID(as_uuid=True), nullable=False)
    assignment_id:          Mapped[uuid.UUID]  = mapped_column(PGUUID(as_uuid=True), nullable=False)
    title:                  Mapped[str]        = mapped_column(String(500), nullable=False)
    knowledge_area:         Mapped[str | None] = mapped_column(String(255), nullable=True)
    status:                 Mapped[str]        = mapped_column(String(50), default="in_progress")
    progress_percent:       Mapped[float]      = mapped_column(Float, default=0.0)
    estimated_defense_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at:             Mapped[datetime]   = mapped_column(DateTime(timezone=True))
    updated_at:             Mapped[datetime]   = mapped_column(DateTime(timezone=True))

class Milestone(Base):
    __tablename__ = "milestones"
    __table_args__ = {"schema": "ti"}
    id:              Mapped[uuid.UUID]       = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ti_id:           Mapped[uuid.UUID]       = mapped_column(PGUUID(as_uuid=True), nullable=False)
    name:            Mapped[str]             = mapped_column(String(255), nullable=False)
    description:     Mapped[str | None]      = mapped_column(Text, nullable=True)
    due_date:        Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_date:  Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status:          Mapped[str]             = mapped_column(String(50), default="pending")
    order_index:     Mapped[int]             = mapped_column(Integer, default=0)
    created_at:      Mapped[datetime]        = mapped_column(DateTime(timezone=True))

class ProgressAdvance(Base):
    __tablename__ = "progress_advances"
    __table_args__ = {"schema": "ti"}
    id:               Mapped[uuid.UUID]  = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ti_id:            Mapped[uuid.UUID]  = mapped_column(PGUUID(as_uuid=True), nullable=False)
    milestone_id:     Mapped[uuid.UUID | None] = mapped_column(PGUUID(as_uuid=True), nullable=True)
    description:      Mapped[str]        = mapped_column(Text, nullable=False)
    activities_done:  Mapped[str | None] = mapped_column(Text, nullable=True)
    obstacles:        Mapped[str | None] = mapped_column(Text, nullable=True)
    progress_percent: Mapped[float]      = mapped_column(Float, default=0.0)
    registered_by:    Mapped[uuid.UUID]  = mapped_column(PGUUID(as_uuid=True), nullable=False)
    registered_at:    Mapped[datetime]   = mapped_column(DateTime(timezone=True))

class DelayAlert(Base):
    __tablename__ = "delay_alerts"
    __table_args__ = {"schema": "ti"}
    id:             Mapped[uuid.UUID]       = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ti_id:          Mapped[uuid.UUID]       = mapped_column(PGUUID(as_uuid=True), nullable=False)
    milestone_id:   Mapped[uuid.UUID | None]= mapped_column(PGUUID(as_uuid=True), nullable=True)
    level:          Mapped[int]             = mapped_column(Integer, nullable=False)
    reason:         Mapped[str | None]      = mapped_column(Text, nullable=True)
    status:         Mapped[str]             = mapped_column(String(50), default="active")
    detected_at:    Mapped[datetime]        = mapped_column(DateTime(timezone=True))
    resolved_at:    Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

class TutoringSession(Base):
    __tablename__ = "tutoring_sessions"
    __table_args__ = {"schema": "sessions"}
    id:            Mapped[uuid.UUID]       = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ti_id:         Mapped[uuid.UUID]       = mapped_column(PGUUID(as_uuid=True), nullable=False)
    tutor_id:      Mapped[uuid.UUID]       = mapped_column(PGUUID(as_uuid=True), nullable=False)
    student_id:    Mapped[uuid.UUID]       = mapped_column(PGUUID(as_uuid=True), nullable=False)
    scheduled_at:  Mapped[datetime]        = mapped_column(DateTime(timezone=True), nullable=False)
    duration_min:  Mapped[int]             = mapped_column(Integer, default=60)
    modality:      Mapped[str]             = mapped_column(String(50), default="virtual")
    status:        Mapped[str]             = mapped_column(String(50), default="scheduled")
    agenda:        Mapped[str | None]      = mapped_column(Text, nullable=True)
    meeting_url:   Mapped[str | None]      = mapped_column(String(500), nullable=True)
    created_at:    Mapped[datetime]        = mapped_column(DateTime(timezone=True))
    updated_at:    Mapped[datetime]        = mapped_column(DateTime(timezone=True))

class Notification(Base):
    __tablename__ = "notifications"
    __table_args__ = {"schema": "notif"}
    id:                  Mapped[uuid.UUID]       = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    recipient_id:        Mapped[uuid.UUID]       = mapped_column(PGUUID(as_uuid=True), nullable=False)
    notification_type:   Mapped[str]             = mapped_column(String(50), nullable=False)
    subject:             Mapped[str | None]      = mapped_column(String(255), nullable=True)
    body:                Mapped[str]             = mapped_column(Text, nullable=False)
    is_read:             Mapped[bool]            = mapped_column(Boolean, default=False)
    read_at:             Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at:          Mapped[datetime]        = mapped_column(DateTime(timezone=True))



# ── Seed data ────────────────────────────────────────────────────────────────
TUTORS_DATA = [
    {"email":"cmendoza@sigtpi.edu.co",   "name":"Carlos Mendoza Ruiz",      "area":"Ciberseguridad y Ciberdefensa"},
    {"email":"lvargas@sigtpi.edu.co",    "name":"Laura Vargas Herrera",     "area":"Redes y Telecomunicaciones"},
    {"email":"atorres@sigtpi.edu.co",    "name":"Andrés Torres Molina",     "area":"Ciencia de Datos e IA"},
    {"email":"mrestrepo@sigtpi.edu.co",  "name":"María Restrepo Gómez",     "area":"Ingeniería de Software"},
    {"email":"jsanchez@sigtpi.edu.co",   "name":"Jorge Sánchez López",      "area":"Gestión de Sistemas"},
]
STUDENTS_DATA = [
    {"email":"abermudez@est.sigtpi.edu.co",  "name":"Alejandro Bermúdez Castro"},
    {"email":"cmora@est.sigtpi.edu.co",      "name":"Catalina Mora Jiménez"},
    {"email":"dpineda@est.sigtpi.edu.co",    "name":"Diego Pineda Suárez"},
    {"email":"egomez@est.sigtpi.edu.co",     "name":"Elena Gómez Parra"},
    {"email":"frios@est.sigtpi.edu.co",      "name":"Felipe Ríos Mendez"},
    {"email":"gsalazar@est.sigtpi.edu.co",   "name":"Gloria Salazar Vera"},
    {"email":"hlopez@est.sigtpi.edu.co",     "name":"Héctor López Rueda"},
    {"email":"icastro@est.sigtpi.edu.co",    "name":"Isabel Castro Niño"},
    {"email":"jramirez@est.sigtpi.edu.co",   "name":"Julio Ramírez Ortiz"},
    {"email":"kgarcia@est.sigtpi.edu.co",    "name":"Karen García Soto"},
]
TI_TITLES = [
    "Detección de intrusiones en redes OT mediante machine learning",
    "Marco de ciberseguridad para infraestructuras críticas nacionales",
    "Análisis forense digital en entornos cloud híbridos",
    "Modelo de gestión de riesgos para sistemas SCADA",
    "Arquitectura Zero Trust para ministerios públicos colombianos",
    "Inteligencia artificial aplicada a la detección de APTs",
    "Seguridad en comunicaciones satelitales para defensa",
    "Análisis de vulnerabilidades en sistemas de votación electrónica",
    "Protocolo de respuesta a incidentes para entidades del Estado",
    "Criptografía post-cuántica en infraestructura PKI nacional",
]

async def seed_data(session):
    """Insert initial data — only if tables are empty."""
    # Check if already seeded
    result = await session.execute(text("SELECT COUNT(*) FROM public.users"))
    if result.scalar() > 0:
        print("  ℹ️  Data already exists — skipping seed (use --force to override)")
        return False

    import bcrypt as _bcrypt
    from sigtpi_common.security.password import hash_password

    now = datetime.now(timezone.utc)

    # ── Fixed users ──────────────────────────────────────────────────────────
    admin_id = uuid.uuid4()
    coo_id   = uuid.uuid4()
    dir_id   = uuid.uuid4()

    fixed_users = [
        (admin_id, "admin@sigtpi.edu.co",          "Admin1234!@",   "Administrador SIGTPI",    True),
        (coo_id,   "coordinacion@sigtpi.edu.co",   "Coord1234!@",   "Coordinación Académica",  False),
        (dir_id,   "direccion@sigtpi.edu.co",       "Direct1234!@",  "Dirección de Programa",   False),
    ]
    for uid, email, pw, name, superuser in fixed_users:
        h = hash_password(pw)
        session.add(AuthUser(id=uid, email=email, hashed_password=h, full_name=name,
                             is_active=True, is_superuser=superuser,
                             totp_enabled=False, failed_login_attempts=0,
                             created_at=now, updated_at=now))
        session.add(UserProfile(id=uid, email=email, full_name=name,
                                is_superuser=superuser, status="active",
                                created_at=now, updated_at=now))
    await session.flush()

    # ── Fixed roles ──────────────────────────────────────────────────────────
    session.add(UserRole(id=uuid.uuid4(), user_id=admin_id, role_code="ADM",
                         is_active=True, assigned_at=now))
    session.add(UserRole(id=uuid.uuid4(), user_id=coo_id,   role_code="COO",
                         is_active=True, assigned_at=now))
    session.add(UserRole(id=uuid.uuid4(), user_id=dir_id,   role_code="DIR",
                         is_active=True, assigned_at=now))
    await session.flush()

    # ── Program ──────────────────────────────────────────────────────────────
    prog_id = uuid.uuid4()
    session.add(Program(
        id=prog_id, code="MCCS-01",
        name="Maestría en Ciberseguridad y Ciberdefensa",
        level="maestria", duration_semesters=4, duration_months=24,
        max_students_per_tutor=5, min_gpa_for_ti=3.5,
        description="Programa de maestría orientado a la seguridad de sistemas de información y defensa cibernética.",
        coordinator_email="coordinacion@sigtpi.edu.co",
        status="active", created_at=now, updated_at=now
    ))
    await session.flush()

    # ── Tutors ───────────────────────────────────────────────────────────────
    tutor_ids = []
    for t in TUTORS_DATA:
        tid = uuid.uuid4()
        h = hash_password("Tutor1234!@")
        session.add(AuthUser(id=tid, email=t["email"], hashed_password=h,
                             full_name=t["name"], is_active=True, is_superuser=False,
                             totp_enabled=False, failed_login_attempts=0,
                             created_at=now, updated_at=now))
        session.add(UserProfile(id=tid, email=t["email"], full_name=t["name"],
                                area_of_expertise=t["area"], is_superuser=False,
                                status="active", created_at=now, updated_at=now))
        session.add(UserRole(id=uuid.uuid4(), user_id=tid, role_code="TUT",
                             program_id=prog_id, is_active=True, assigned_at=now))
        tutor_ids.append(tid)
    await session.flush()

    # ── Students + TIs ───────────────────────────────────────────────────────
    student_ids = []
    for s in STUDENTS_DATA:
        sid = uuid.uuid4()
        h = hash_password("Est1234!@")
        session.add(AuthUser(id=sid, email=s["email"], hashed_password=h,
                             full_name=s["name"], is_active=True, is_superuser=False,
                             totp_enabled=False, failed_login_attempts=0,
                             created_at=now, updated_at=now))
        session.add(UserProfile(id=sid, email=s["email"], full_name=s["name"],
                                is_superuser=False, status="active",
                                created_at=now, updated_at=now))
        session.add(UserRole(id=uuid.uuid4(), user_id=sid, role_code="EST",
                             program_id=prog_id, is_active=True, assigned_at=now))
        session.add(Enrollment(id=uuid.uuid4(), student_id=sid, program_id=prog_id,
                               status="active", enrolled_at=now))
        student_ids.append(sid)
    await session.flush()

    # ── Assignments + TIs ────────────────────────────────────────────────────
    for i, (sid, title) in enumerate(zip(student_ids, TI_TITLES)):
        tutor_id = tutor_ids[i % len(tutor_ids)]
        assign_id = uuid.uuid4()
        ti_id = uuid.uuid4()

        session.add(TutorAssignment(
            id=assign_id, student_id=sid, tutor_id=tutor_id, program_id=prog_id,
            status="active", area="Ciberseguridad", title=title,
            assigned_by=coo_id, created_at=now, updated_at=now
        ))
        session.add(ResearchWork(
            id=ti_id, student_id=sid, assignment_id=assign_id, title=title,
            knowledge_area="Ciberseguridad y Ciberdefensa",
            status="in_progress", progress_percent=round(10 + i*8, 1),
            created_at=now, updated_at=now
        ))

        # Milestones
        milestones = [
            ("Aprobación de anteproyecto", 30, "approved" if i > 2 else "pending"),
            ("Entrega de marco teórico",    60, "in_progress" if i > 4 else "pending"),
            ("Borrador final",              90, "pending"),
            ("Defensa",                    120, "pending"),
        ]
        for mname, days_offset, mstatus in milestones:
            from datetime import timedelta
            session.add(Milestone(
                id=uuid.uuid4(), ti_id=ti_id, name=mname,
                status=mstatus, order_index=milestones.index((mname,days_offset,mstatus)),
                due_date=now + timedelta(days=days_offset), created_at=now
            ))

        # Session
        from datetime import timedelta
        session.add(TutoringSession(
            id=uuid.uuid4(), ti_id=ti_id, tutor_id=tutor_id, student_id=sid,
            scheduled_at=now + timedelta(days=7), duration_min=60,
            modality="virtual", status="scheduled", created_at=now, updated_at=now
        ))

        # Notification
        session.add(Notification(
            id=uuid.uuid4(), recipient_id=sid,
            notification_type="assignment",
            subject="Tutor asignado",
            body=f"Se te ha asignado el tutor para tu TI: {title[:50]}",
            is_read=False, created_at=now
        ))

    await session.commit()
    print(f"  ✓ {len(fixed_users)} usuarios base + {len(TUTORS_DATA)} tutores + {len(STUDENTS_DATA)} estudiantes")
    print(f"  ✓ 1 programa + {len(TI_TITLES)} TIs + milestones + sesiones + notificaciones")
    return True


# ── Main ─────────────────────────────────────────────────────────────────────
async def main():
    import sys
    force = "--force" in sys.argv

    print("\n╔══════════════════════════════════════════════╗")
    print("║  SIGTPI — Database Initialization           ║")
    print("╚══════════════════════════════════════════════╝\n")

    await wait_for_postgres()

    engine = create_async_engine(DB_URL, echo=False, connect_args=CONNECT_ARGS)
    Session = async_sessionmaker(engine, expire_on_commit=False)

    # 1. Create schemas
    print("📂 Creating schemas...")
    async with engine.begin() as conn:
        for schema in SCHEMAS:
            await conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema}"))
        print(f"  ✓ {', '.join(SCHEMAS)}")

    # 2. Create tables (IF NOT EXISTS)
    print("\n📋 Creating tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("  ✓ All tables created (IF NOT EXISTS)")

    # 3. Run column migrations (ADD COLUMN IF NOT EXISTS)
    print("\n🔧 Column migrations...")
    async with engine.begin() as conn:
        await run_migrations(conn)

    # 4. Seed data
    print("\n🌱 Seeding initial data...")
    async with Session() as session:
        if force:
            print("  ⚠️  --force flag: clearing existing data...")
            await session.execute(text("TRUNCATE TABLE public.users CASCADE"))
            await session.commit()
        seeded = await seed_data(session)

    await engine.dispose()

    print("\n✅ Database ready!")
    print("   Login: admin@sigtpi.edu.co / Admin1234!@")
    print("          coordinacion@sigtpi.edu.co / Coord1234!@")
    print("          cmendoza@sigtpi.edu.co / Tutor1234!@")
    print("          abermudez@est.sigtpi.edu.co / Est1234!@\n")


if __name__ == "__main__":
    asyncio.run(main())
