This background task publishes interval measurements to a local DB.

Those measurements have the form:

{
    'pc_id': pc_id,
    'total_power_consumption': total_power_consumption,
    'tasks': task_metrics,
    'start_time': format_time(start_time),
    'stop_time': format_time(stop_time),
    'platform': platform.platform(),
}