"""
report-service — KPIs y dashboards con datos reales de la BD compartida.
Usa el mismo postgres con search_path configurado para acceder a todos los esquemas.
"""
from uuid import UUID
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.schemas.report import (
    TIStatusKPI, TutorWorkloadKPI, ProgramKPI,
    StudentProgressReport, DashboardSummary,
)
from sigtpi_common.utils.logging import get_logger

logger = get_logger(__name__)


async def get_dashboard_summary(
    db: AsyncSession,
    program_id: UUID | None = None,
) -> DashboardSummary:
    """Dashboard ejecutivo — consultas SQL directas a la BD compartida."""
    try:
        # TIs activos
        r_ti = await db.execute(text(
            "SELECT COUNT(*) FROM ti.research_works WHERE status NOT IN ('withdrawn','completed')"
        ))
        total_tis = r_ti.scalar() or 0

        # TIs en riesgo (alertas nivel 3+)
        r_risk = await db.execute(text(
            "SELECT COUNT(DISTINCT ti_id) FROM ti.delay_alerts WHERE level >= 3 AND status='active'"
        ))
        at_risk = r_risk.scalar() or 0

        # Estudiantes activos (con TI activo)
        r_stu = await db.execute(text(
            "SELECT COUNT(DISTINCT student_id) FROM ti.research_works WHERE status NOT IN ('withdrawn','completed')"
        ))
        total_students = r_stu.scalar() or 0

        # Tutores activos
        r_tut = await db.execute(text(
            "SELECT COUNT(DISTINCT tutor_id) FROM tutoring.tutor_assignments WHERE status='active'"
        ))
        total_tutors = r_tut.scalar() or 0

        # Sesiones esta semana
        r_ses = await db.execute(text(
            "SELECT COUNT(*) FROM sessions.tutoring_sessions "
            "WHERE scheduled_at >= NOW() - INTERVAL '7 days' AND status='completed'"
        ))
        sessions_week = r_ses.scalar() or 0

        # Evaluaciones pendientes
        r_eval = await db.execute(text(
            "SELECT COUNT(*) FROM evaluation.evaluations WHERE status='pending' OR status='in_progress'"
        ) if await _table_exists(db, 'evaluation', 'evaluations') else text("SELECT 0"))
        pending_evals = r_eval.scalar() or 0

        # Alertas activas
        r_alerts = await db.execute(text(
            "SELECT COUNT(*) FROM ti.delay_alerts WHERE status='active'"
        ))
        active_alerts = r_alerts.scalar() or 0

        # Carga de tutores
        r_workload = await db.execute(text("""
            SELECT u.full_name, ta.tutor_id,
                   COUNT(DISTINCT rw.id) as active_tis
            FROM tutoring.tutor_assignments ta
            JOIN users.users u ON u.id = ta.tutor_id
            LEFT JOIN ti.research_works rw ON rw.assignment_id = ta.id
                AND rw.status NOT IN ('withdrawn','completed')
            WHERE ta.status = 'active'
            GROUP BY ta.tutor_id, u.full_name
            ORDER BY active_tis DESC
            LIMIT 10
        """))
        tutor_workload = [
            {"tutor_id": str(row.tutor_id), "full_name": row.full_name, "active_tis": row.active_tis}
            for row in r_workload.fetchall()
        ]

        # Graduation rate (completed in expected time)
        r_grad = await db.execute(text("""
            SELECT
                COUNT(*) FILTER (WHERE status='completed') as completed,
                COUNT(*) as total
            FROM ti.research_works
            WHERE created_at < NOW() - INTERVAL '6 months'
        """))
        grad_row = r_grad.fetchone()
        grad_rate = round((grad_row.completed / grad_row.total * 100), 1) if grad_row and grad_row.total > 0 else None

        # Avg sessions per TI
        r_avg_ses = await db.execute(text("""
            SELECT ROUND(AVG(session_count)::numeric, 1) FROM (
                SELECT ti_id, COUNT(*) as session_count
                FROM sessions.tutoring_sessions
                WHERE status = 'completed'
                GROUP BY ti_id
            ) s
        """))
        avg_sessions = r_avg_ses.scalar()

        return DashboardSummary(
            generated_at=datetime.now(timezone.utc),
            total_students=total_students,
            total_tutors=total_tutors,
            total_tis=total_tis,
            active_tis=total_tis,
            tis_at_risk=at_risk,
            at_risk_tis=at_risk,
            sessions_this_week=sessions_week,
            pending_evaluations=pending_evals,
            unread_alerts=active_alerts,
            active_alerts=active_alerts,
            graduation_rate=grad_rate,
            avg_sessions_per_ti=float(avg_sessions) if avg_sessions else None,
            tutor_workload=tutor_workload,
            recent_activity=[],
        )
    except Exception as e:
        logger.error("dashboard_error", error=str(e))
        return DashboardSummary(
            generated_at=datetime.now(timezone.utc),
            total_students=0, total_tutors=0, total_tis=0,
            tis_at_risk=0, sessions_this_week=0,
            pending_evaluations=0, unread_alerts=0,
            recent_activity=[],
        )


async def _table_exists(db: AsyncSession, schema: str, table: str) -> bool:
    r = await db.execute(text(
        "SELECT 1 FROM information_schema.tables "
        "WHERE table_schema=:s AND table_name=:t"
    ), {"s": schema, "t": table})
    return r.fetchone() is not None


async def get_ti_status_kpi(
    db: AsyncSession,
    program_id: UUID | None = None,
) -> TIStatusKPI:
    try:
        r = await db.execute(text("""
            SELECT
                COUNT(*) as total,
                COUNT(*) FILTER (WHERE status='in_progress') as active,
                COUNT(*) FILTER (WHERE status='approved' OR status='completed') as approved,
                COUNT(*) FILTER (WHERE status='withdrawn') as withdrawn
            FROM ti.research_works
        """))
        row = r.fetchone()

        r_risk = await db.execute(text(
            "SELECT COUNT(DISTINCT ti_id) FROM ti.delay_alerts WHERE level >= 3 AND status='active'"
        ))
        at_risk = r_risk.scalar() or 0

        r_avg = await db.execute(text(
            "SELECT ROUND(AVG(progress_percent)::numeric, 1) FROM ti.research_works "
            "WHERE status='in_progress'"
        ))
        avg_progress = float(r_avg.scalar() or 0)

        return TIStatusKPI(
            total_tis=row.total or 0,
            total=row.total or 0,
            active=row.active or 0,
            in_progress=row.active or 0,
            approved=row.approved or 0,
            withdrawn=row.withdrawn or 0,
            at_risk=at_risk,
            avg_progress=avg_progress,
            avg_months_to_defense=None,
        )
    except Exception as e:
        logger.error("ti_status_error", error=str(e))
        return TIStatusKPI(total_tis=0, active=0, approved=0, withdrawn=0,
                           at_risk=0, avg_progress=0.0, avg_months_to_defense=None)


async def get_tutor_workload(db: AsyncSession, tutor_id: UUID) -> TutorWorkloadKPI:
    try:
        r = await db.execute(text("""
            SELECT
                COUNT(DISTINCT rw.student_id) as active_students,
                COUNT(DISTINCT s.id) FILTER (
                    WHERE s.scheduled_at >= NOW() - INTERVAL '30 days'
                    AND s.status='completed'
                ) as sessions_month,
                COUNT(DISTINCT rw.id) as active_tis
            FROM tutoring.tutor_assignments ta
            LEFT JOIN ti.research_works rw ON rw.assignment_id = ta.id
            LEFT JOIN sessions.tutoring_sessions s ON s.ti_id = rw.id
            WHERE ta.tutor_id = :tid AND ta.status = 'active'
        """), {"tid": str(tutor_id)})
        row = r.fetchone()
        return TutorWorkloadKPI(
            tutor_id=tutor_id,
            active_students=row.active_students or 0,
            active_tis=row.active_tis or 0,
            sessions_this_month=row.sessions_month or 0,
            pending_reviews=0,
            avg_response_days=0.0,
        )
    except Exception as e:
        logger.error("tutor_workload_error", error=str(e))
        return TutorWorkloadKPI(tutor_id=tutor_id, active_students=0,
                                sessions_this_month=0, pending_reviews=0, avg_response_days=0.0)


async def get_program_kpis(db: AsyncSession, program_id: UUID) -> ProgramKPI:
    try:
        r = await db.execute(text("""
            SELECT p.name,
                COUNT(DISTINCT e.student_id) as active_students,
                COUNT(DISTINCT ta.tutor_id) as tutor_count
            FROM academic.programs p
            LEFT JOIN academic.enrollments e ON e.program_id = p.id AND e.status='active'
            LEFT JOIN tutoring.tutor_assignments ta ON ta.program_id = p.id AND ta.status='active'
            WHERE p.id = :pid
            GROUP BY p.name
        """), {"pid": str(program_id)})
        row = r.fetchone()
        return ProgramKPI(
            program_id=program_id,
            program_name=row.name if row else "Programa",
            graduation_rate=0.0,
            avg_duration_months=0.0,
            active_students=row.active_students if row else 0,
            at_risk_students=0,
            tutor_count=row.tutor_count if row else 0,
        )
    except Exception as e:
        logger.error("program_kpis_error", error=str(e))
        return ProgramKPI(program_id=program_id, program_name="Programa",
                          graduation_rate=0.0, avg_duration_months=0.0,
                          active_students=0, at_risk_students=0, tutor_count=0)


async def get_student_report(db: AsyncSession, student_id: UUID) -> StudentProgressReport:
    try:
        r = await db.execute(text("""
            SELECT rw.id, rw.title, rw.status, rw.progress_percent,
                   e.program_id,
                   (SELECT COUNT(*) FROM sessions.tutoring_sessions s
                    WHERE s.ti_id = rw.id AND s.status='completed') as sessions_done,
                   (SELECT COUNT(*) FROM ti.milestones m
                    WHERE m.ti_id = rw.id AND m.status='approved') as milestones_done,
                   (SELECT COUNT(*) FROM ti.milestones m WHERE m.ti_id = rw.id) as milestones_total,
                   (SELECT COUNT(*) FROM ti.delay_alerts a
                    WHERE a.ti_id = rw.id AND a.status='active') as alerts
            FROM ti.research_works rw
            LEFT JOIN academic.enrollments e ON e.student_id = rw.student_id AND e.status='active'
            WHERE rw.student_id = :sid
            ORDER BY rw.created_at DESC LIMIT 1
        """), {"sid": str(student_id)})
        row = r.fetchone()
        if not row:
            return StudentProgressReport(
                student_id=student_id, program_id=UUID(int=0),
                ti_id=None, ti_title=None, status="no_ti",
                progress_percent=0.0, sessions_completed=0,
                milestones_approved=0, milestones_total=0,
                active_alerts=0, next_milestone=None, next_milestone_date=None,
            )
        return StudentProgressReport(
            student_id=student_id,
            program_id=row.program_id or UUID(int=0),
            ti_id=row.id, ti_title=row.title, status=row.status,
            progress_percent=float(row.progress_percent or 0),
            sessions_completed=row.sessions_done or 0,
            milestones_approved=row.milestones_done or 0,
            milestones_total=row.milestones_total or 0,
            active_alerts=row.alerts or 0,
            next_milestone=None, next_milestone_date=None,
        )
    except Exception as e:
        logger.error("student_report_error", error=str(e))
        return StudentProgressReport(
            student_id=student_id, program_id=UUID(int=0),
            ti_id=None, ti_title=None, status="error",
            progress_percent=0.0, sessions_completed=0,
            milestones_approved=0, milestones_total=0,
            active_alerts=0, next_milestone=None, next_milestone_date=None,
        )
