import math
import uuid

def format_duration_to_string(seconds):
    '''convert seconds to ui string'''
    if not isinstance(seconds, (int, float)) or seconds < 0:
        return 'N/A'

    if seconds == 0:
        return '0s'

    hours = math.floor(seconds / 3600)
    remaining_seconds_after_hours = seconds % 3600
    minutes = math.floor(remaining_seconds_after_hours / 60)
    remaining_seconds_final = math.floor(remaining_seconds_after_hours % 60)

    parts = []
    if hours > 0:
        parts.append(f'{int(hours)}h')
    if minutes > 0:
        parts.append(f'{int(minutes)}min')

    if not parts and remaining_seconds_final > 0:
        parts.append(f'{int(remaining_seconds_final)}s')
    elif not parts and seconds > 0:
        return '<1s'

    return ' '.join(parts) if parts else '0s'

def check_csrf_token(session, form):
    '''Check csrf token'''
    token = form.get('csrf_token')
    return token and token == session.get('csrf_token')

def generate_csrf_token(session):
    '''UUID for csrf token'''
    token = str(uuid.uuid4())
    session['csrf_token'] = token
    return token
