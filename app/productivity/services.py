import logging
from datetime import datetime, timezone
from app.extensions import db
from app.models.study_session import StudySession
from app.models.study_goal import StudyGoal
from app.models.points import PointsLog
from app.points.services import award_points, record_activity
from app.productivity.timers import PersonalTimerStorage
from app.productivity.analytics import AnalyticsService

logger = logging.getLogger(__name__)


class ProductivityService:
    """Business logic for study productivity, session logging, and rewards."""

    @staticmethod
    def complete_session(user, duration_minutes, session_type='focus', subject=None, group_id=None):
        """
        Record a completed study session.
        If session_type is 'focus', awards +2 points and updates study streak.
        Break sessions or incomplete sessions award 0 points.
        """
        if duration_minutes <= 0:
            raise ValueError("Duration must be positive.")

        session = StudySession(
            user_id=user.id,
            subject=subject or 'General',
            duration_minutes=duration_minutes,
            completed=True,
            session_type=session_type,
            group_id=group_id,
            started_at=datetime.now(timezone.utc),
            completed_at=datetime.now(timezone.utc)
        )
        db.session.add(session)
        db.session.commit()

        points_awarded = 0
        if session_type == 'focus':
            # Award +2 points for focus completion
            award_points(user, 2, PointsLog.REASON_STUDY_SESSION, reference_id=session.id)
            points_awarded = 2

            # Record study streak activity
            record_activity(user, 'study_session')

            # Update active uncompleted study goals
            active_goals = StudyGoal.query.filter_by(user_id=user.id, completed=False).all()
            for goal in active_goals:
                was_completed = goal.completed
                goal.add_progress(duration_minutes)
                if not was_completed and goal.completed:
                    from app.notifications.services import create_notification
                    create_notification(
                        user_id=user.id,
                        sender_id=None,
                        notification_type='goal',
                        title="Goal Completed!",
                        message=f"Congratulations! You completed your study goal: '{goal.title}'!",
                        link_url="/productivity/"
                    )

            from app.notifications.services import create_notification
            create_notification(
                user_id=user.id,
                sender_id=None,
                notification_type='pomodoro',
                title="Focus Session Completed",
                message=f"Great job finishing a {duration_minutes}-minute focus session! (+2 pts)",
                link_url="/productivity/"
            )

            # Invalidate memoized analytics cache
            AnalyticsService.invalidate_cache(user.id)

            logger.info(f"[PRODUCTIVITY LOG] action=focus_completed user_id={user.id} duration={duration_minutes}m points=+2")
        else:
            logger.info(f"[PRODUCTIVITY LOG] action=break_completed user_id={user.id} duration={duration_minutes}m")

        # Clear personal timer state
        PersonalTimerStorage.clear_state(user.id)

        return {
            'session_id': session.id,
            'points_awarded': points_awarded,
            'new_total_points': user.total_points,
            'current_streak': user.current_streak
        }
