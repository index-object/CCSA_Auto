from datetime import datetime, timezone, timedelta
from dateutil import tz

SHANGHAI_TZ = timezone(timedelta(hours=8))


def get_current_time():
    """获取当前上海时间"""
    return datetime.now(SHANGHAI_TZ)


def get_current_utc_time():
    """获取当前UTC时间"""
    return datetime.now(timezone.utc)


def utc_to_shanghai(utc_dt):
    """将UTC时间转换为上海时间"""
    if utc_dt is None:
        return None
    if utc_dt.tzinfo is None:
        utc_dt = utc_dt.replace(tzinfo=timezone.utc)
    return utc_dt.astimezone(SHANGHAI_TZ)


def shanghai_to_utc(shanghai_dt):
    """将上海时间转换为UTC时间"""
    if shanghai_dt is None:
        return None
    if shanghai_dt.tzinfo is None:
        shanghai_dt = shanghai_dt.replace(tzinfo=SHANGHAI_TZ)
    return shanghai_dt.astimezone(timezone.utc)


def format_datetime_for_display(utc_dt, format_str="%Y-%m-%d %H:%M:%S"):
    """将UTC时间格式化为上海本地时间字符串"""
    if utc_dt is None:
        return "未设置"
    shanghai_dt = utc_to_shanghai(utc_dt)
    return shanghai_dt.strftime(format_str)


def format_datetime_short(utc_dt):
    """将UTC时间格式化为短格式（用于列表显示）"""
    return format_datetime_for_display(utc_dt, "%Y-%m-%d %H:%M")


def format_datetime_date(utc_dt):
    """将UTC时间格式化为日期格式"""
    return format_datetime_for_display(utc_dt, "%Y-%m-%d")


def format_datetime_time(utc_dt):
    """将UTC时间格式化为时间格式"""
    return format_datetime_for_display(utc_dt, "%H:%M:%S")


def parse_to_shanghai(dt_str, format_str="%Y-%m-%d %H:%M:%S"):
    """将字符串解析为上海时间"""
    if dt_str is None:
        return None
    naive_dt = datetime.strptime(dt_str, format_str)
    return naive_dt.replace(tzinfo=SHANGHAI_TZ)


def ensure_shanghai_timezone(dt):
    """确保datetime对象有时区信息（上海时区）"""
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=SHANGHAI_TZ)
    return dt


def ensure_utc_timezone(dt):
    """确保datetime对象有时区信息（UTC时区）"""
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def calculate_next_run_time_utc(task, last_executed_at=None):
    """根据任务类型和配置计算下次运行时间（返回UTC时间）

    Args:
        task: 任务对象
        last_executed_at: 上次执行时间（上海时间），默认为None

    Returns:
        datetime: 下次运行时间（UTC时间）
    """
    import random
    from datetime import datetime as dt

    if last_executed_at is None:
        last_executed_at = get_current_time()

    last_executed_at = ensure_shanghai_timezone(last_executed_at)

    task_type = task.task_type

    if task_type == "daily":
        hour_range = (7, 11)
        minute_range = (0, 59)

        hour = random.randint(hour_range[0], hour_range[1])
        minute = random.randint(minute_range[0], minute_range[1])

        last_date = last_executed_at.date()
        next_run_date = last_date + timedelta(days=1)

        next_run_shanghai = dt(
            next_run_date.year, next_run_date.month, next_run_date.day, hour, minute, 0
        )
        next_run_shanghai = next_run_shanghai.replace(tzinfo=SHANGHAI_TZ)

        return shanghai_to_utc(next_run_shanghai)

    elif task_type == "weekly":
        from ccsa_auto.core.config import Config

        weekday = Config.TASK_DETAILS["WEEKLY"]["weekday"]
        hour_range = (8, 11)
        minute_range = (0, 59)

        hour = random.randint(hour_range[0], hour_range[1])
        minute = random.randint(minute_range[0], minute_range[1])

        last_date = last_executed_at.date()

        days_until = 7

        next_run_date = last_date + timedelta(days=days_until)

        next_run_shanghai = dt(
            next_run_date.year, next_run_date.month, next_run_date.day, hour, minute, 0
        )
        next_run_shanghai = next_run_shanghai.replace(tzinfo=SHANGHAI_TZ)

        return shanghai_to_utc(next_run_shanghai)

    elif task_type == "monthly":
        from ccsa_auto.core.config import Config

        day = Config.TASK_DETAILS["MONTHLY"]["day"]
        hour_range = (9, 15)
        minute_range = (0, 59)

        hour = random.randint(hour_range[0], hour_range[1])
        minute = random.randint(minute_range[0], minute_range[1])

        last_date = last_executed_at.date()

        if last_date.month == 12:
            next_year = last_date.year + 1
            next_month = 1
        else:
            next_year = last_date.year
            next_month = last_date.month + 1

        next_run_date = last_date.replace(year=next_year, month=next_month, day=day)
        if next_run_date <= last_date:
            if next_run_date.month == 12:
                next_run_date = next_run_date.replace(
                    year=next_run_date.year + 1, month=1
                )
            else:
                next_run_date = next_run_date.replace(month=next_run_date.month + 1)

        next_run_shanghai = dt(
            next_run_date.year, next_run_date.month, next_run_date.day, hour, minute, 0
        )
        next_run_shanghai = next_run_shanghai.replace(tzinfo=SHANGHAI_TZ)

        return shanghai_to_utc(next_run_shanghai)
    else:
        return get_current_utc_time() + timedelta(days=1)
