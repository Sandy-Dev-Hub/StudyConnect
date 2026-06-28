from app.extensions import db
from app.models.group import StudyGroup, GroupMember
from app.models.points import PointsLog

def create_group(form_data, creator):
    group = StudyGroup(
        name=form_data['name'],
        description=form_data.get('description', ''),
        subject_tag=form_data.get('subject_tag') or None,
        exam_tag=form_data.get('exam_tag') or None,
        is_private=form_data.get('is_private', False),
        avatar_color=form_data.get('avatar_color', '#EA8528'),
        creator_id=creator.id
    )
    db.session.add(group)
    db.session.flush()

    # Add creator as admin
    member = GroupMember(group_id=group.id, user_id=creator.id, role='admin')
    db.session.add(member)
    db.session.commit()
    return group

def update_group(group, form_data):
    group.name = form_data['name']
    group.description = form_data.get('description', '')
    group.subject_tag = form_data.get('subject_tag') or None
    group.exam_tag = form_data.get('exam_tag') or None
    group.is_private = form_data.get('is_private', False)
    if form_data.get('avatar_color'):
        group.avatar_color = form_data['avatar_color']
    db.session.commit()
    return group

def delete_group(group):
    db.session.delete(group)
    db.session.commit()

def join_group(group, user):
    if group.is_member(user.id):
        return False, "You are already a member of this community."
    if group.is_private and group.creator_id != user.id:
        # For simplicity in 2A, private groups can be joined via invite or direct join if link shared
        pass
    member = GroupMember(group_id=group.id, user_id=user.id, role='member')
    db.session.add(member)
    db.session.commit()
    return True, f"Successfully joined {group.name}!"

def leave_group(group, user):
    if group.creator_id == user.id:
        return False, "Group creators cannot leave. Delete the group instead or transfer ownership."
    member = group.members.filter_by(user_id=user.id).first()
    if not member:
        return False, "You are not a member of this group."
    db.session.delete(member)
    db.session.commit()
    return True, f"You have left {group.name}."

def update_member_role(group, admin_user, target_user_id, new_role):
    if not group.is_admin(admin_user.id):
        return False, "Unauthorized: Admin privileges required."
    if group.creator_id == target_user_id:
        return False, "Cannot modify the group creator's role."
    member = group.members.filter_by(user_id=target_user_id).first()
    if not member:
        return False, "Member not found."
    if new_role not in ['admin', 'member']:
        return False, "Invalid role."
    member.role = new_role
    db.session.commit()
    return True, f"Updated role to {new_role}."

def remove_member(group, admin_user, target_user_id):
    if not group.is_admin(admin_user.id):
        return False, "Unauthorized: Admin privileges required."
    if group.creator_id == target_user_id:
        return False, "Cannot remove the group creator."
    member = group.members.filter_by(user_id=target_user_id).first()
    if not member:
        return False, "Member not found."
    db.session.delete(member)
    db.session.commit()
    return True, "Member removed from the community."
