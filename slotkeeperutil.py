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

def fill_in_device_list(session, db, devices):
    '''build device list for ui'''
    device_data = []
    user = db.get_user_by_username(session['username'])

    for device in devices:
        reservation = db.get_active_reservation_for_device(device['id'])
        owned = reservation and reservation['user_id'] == user['id'] if reservation else False
        desc = device['description'] or ''

        # cut excessive long description to preview
        lines = desc.splitlines()
        preview = '\n'.join(lines[:3])[:250]
        if len(desc) > 250 or desc.count('\n') >= 3:
            preview += '\n...'

        device_data.append(
            {
                'device': device,
                'reservation': reservation,
                'user_owned': owned,
                'preview': preview
            }
        )
    return device_data

def generate_pie_chart_segments(device_list, colors, value_key='value', label_key='name',
                                preform_key=None):
    '''generate data to be shown in pie chart. top 3 machines + rest.'''
    pie_data = []
    gradient_parts = []
    total_value = sum(item.get(value_key, 0) for item in device_list)
    cur_angle = 0

    if total_value > 0:
        sorted_data = sorted(device_list, key=lambda x: x.get(value_key, 0), reverse=True)
        top_n = 3
        num_items_total = len(sorted_data)

        pie_items = []
        if num_items_total <= top_n:
            pie_items.extend(sorted_data)
        else:
            pie_items.extend(sorted_data[:top_n])
            others_value = sum(d.get(value_key, 0) for d in sorted_data[top_n:])
            if others_value > 0:
                other_item_data = {label_key: 'Other Devices', value_key: others_value}
                if preform_key == 'formatted_duration':
                    other_item_data[preform_key] = format_duration_to_string(others_value)
                pie_items.append(other_item_data)

        for i, input_list in enumerate(pie_items):
            item_nvalue = input_list.get(value_key, 0)
            percentage = 0
            if total_value > 0:
                percentage = (item_nvalue / total_value) * 100

            # dict to template
            item_dict = {
                'name': input_list.get(label_key, 'Unknown'),
                'value_numeric': item_nvalue,
                'percentage': round(percentage, 1),
                'color': colors[i % len(colors)]
            }

            if preform_key:
                if preform_key in input_list:
                    item_dict[preform_key] = input_list[preform_key]
                else:
                    item_dict[preform_key] = str(item_nvalue)

            pie_data.append(item_dict)

            start_percentage = cur_angle
            is_last_segment = i == len(pie_items) - 1
            if is_last_segment and cur_angle < 100:
                cur_angle = 100.0
            elif total_value > 0 :
                cur_angle += percentage
            cur_angle = min(max(cur_angle, 0), 100.0)
            start_percentage = min(max(start_percentage,0), 100.0)
            gradient_parts.append(
                f'{colors[i % len(colors)]} {round(start_percentage, 2)}% {round(cur_angle, 2)}%'
            )

    conic_gradient_style = ''
    if gradient_parts:
        conic_gradient_style = f'background: conic-gradient({', '.join(gradient_parts)});'
    return pie_data, conic_gradient_style, (total_value > 0)
