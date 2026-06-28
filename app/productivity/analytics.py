import logging
from datetime import datetime, timedelta, timezone, date
from sqlalchemy import func
from app.extensions import db, cache
from app.models.study_session import StudySession
from app.models.study_goal import StudyGoal

logger = logging.getLogger(__name__)


class AnalyticsService:
    """Aggregates study productivity metrics with 5-minute caching."""

    @staticmethod
    @cache.memoize(timeout=300)
    def get_user_analytics(user_id):
        """Calculate comprehensive study analytics for dashboard display."""
        now = datetime.now(timezone.utc)
        thirty_days_ago = now - timedelta(days=30)
        seven_days_ago = now - timedelta(days=7)

        # Base query for completed focus sessions
        base_q = StudySession.query.filter_by(
            user_id=user_id,
            completed=True,
            session_type='focus'
        )

        # Total study time all-time (minutes)
        total_minutes = db.session.query(func.sum(StudySession.duration_minutes)).filter(
            StudySession.user_id == user_id,
            StudySession.completed == True,
            StudySession.session_type == 'focus'
        ).scalar() or 0

        total_hours = round(total_minutes / 60.0, 1)

        # Monthly study hours (last 30 days)
        monthly_minutes = db.session.query(func.sum(StudySession.duration_minutes)).filter(
            StudySession.user_id == user_id,
            StudySession.completed == True,
            StudySession.session_type == 'focus',
            StudySession.completed_at >= thirty_days_ago
        ).scalar() or 0
        monthly_hours = round(monthly_minutes / 60.0, 1)

        # Weekly study hours & 7-day breakdown for bar chart
        weekly_chart_labels = []
        weekly_chart_data = []
        weekly_total_minutes = 0

        for i in range(6, -1, -1):
            day = date.today() - timedelta(days=i)
            start_dt = datetime.combine(day, datetime.min.time(), tzinfo=timezone.utc)
            end_dt = datetime.combine(day, datetime.max.time(), tzinfo=timezone.utc)

            day_mins = db.session.query(func.sum(StudySession.duration_minutes)).filter(
                StudySession.user_id == user_id,
                StudySession.completed == True,
                StudySession.session_type == 'focus',
                StudySession.completed_at >= start_dt,
                StudySession.completed_at <= end_dt
            ).scalar() or 0

            weekly_chart_labels.append(day.strftime('%a'))
            weekly_chart_data.append(round(day_mins / 60.0, 2))
            weekly_total_minutes += day_mins

        weekly_hours = round(weekly_total_minutes / 60.0, 1)

        # Subject breakdown (Pie chart)
        subject_rows = db.session.query(
            StudySession.subject, func.sum(StudySession.duration_minutes)
        ).filter(
            StudySession.user_id == user_id,
            StudySession.completed == True,
            StudySession.session_type == 'focus'
        ).group_by(StudySession.subject).all()

        subject_labels = [r[0] or 'General' for r in subject_rows]
        subject_values = [r[1] for r in subject_rows]

        # Average session duration
        session_count = base_q.count()
        avg_session_duration = round(total_minutes / session_count) if session_count > 0 else 0

        # Goal completion percentage
        active_goals = StudyGoal.query.filter_by(user_id=user_id).all()
        if active_goals:
            completed_goals_count = sum(1 for g in active_goals if g.completed)
            goal_completion_pct = int((completed_goals_count / len(active_goals)) * 100)
        else:
            goal_completion_pct = 0

        # Contribution Heatmap (365 days)
        one_year_ago = now - timedelta(days=365)
        heatmap_rows = db.session.query(
            func.date(StudySession.completed_at), func.sum(StudySession.duration_minutes), func.count(StudySession.id)
        ).filter(
            StudySession.user_id == user_id,
            StudySession.completed == True,
            StudySession.session_type == 'focus',
            StudySession.completed_at >= one_year_ago
        ).group_by(func.date(StudySession.completed_at)).all()

        heatmap_map = {str(r[0])[:10]: {'minutes': int(r[1]), 'count': int(r[2])} for r in heatmap_rows if r[0]}

        return {
            'total_hours': total_hours,
            'total_minutes': total_minutes,
            'monthly_hours': monthly_hours,
            'weekly_hours': weekly_hours,
            'avg_session_duration': avg_session_duration,
            'goal_completion_pct': goal_completion_pct,
            'weekly_chart': {
                'labels': weekly_chart_labels,
                'data': weekly_chart_data
            },
            'subject_chart': {
                'labels': subject_labels,
                'data': subject_values
            },
            'heatmap_data': heatmap_map
        }

    @staticmethod
    def invalidate_cache(user_id):
        """Invalidate memoized analytics cache for a user when new session completes."""
        try:
            cache.delete_memoized(AnalyticsService.get_user_analytics, user_id)
        except Exception as e:
            logger.debug(f"Cache invalidation warning: {e}")
