from datetime import datetime


def struct_time_to_formatted_string(struct_time_obj, time_format='%Y-%m-%dT%H:%M:%S.%fZ'):
    """
    将 struct_time 对象转换为指定格式的字符串
    :param struct_time_obj: struct_time 对象
    :param time_format: 时间格式字符串，默认为 '%Y-%m-%dT%H:%M:%S.%fZ'
    :return: 指定格式的时间字符串
    """
    try:
        # 将 struct_time 对象转换为 datetime 对象
        dt = datetime(*struct_time_obj[:6])

        # 格式化 datetime 对象为指定格式的字符串
        formatted_str = dt.strftime(time_format)

        return formatted_str
    except Exception as e:
        print(f"Error struct_time_to_formatted_string: {e}, use current time")
        return datetime.now().strftime(time_format)
