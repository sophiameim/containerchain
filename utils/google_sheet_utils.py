from oauth2client.service_account import ServiceAccountCredentials
import gspread
from config import google_sheet_config
import datetime
from datetime import timedelta

# 建立通信
CREDS = ServiceAccountCredentials.from_json_keyfile_name(google_sheet_config.json_file_path, google_sheet_config.SCOPE)
CLIENT = gspread.authorize(CREDS)

# 打开指定表单
def get_worksheet(sheet_url, worksheet_name):
    sheet = CLIENT.open_by_url(sheet_url)
    return sheet.worksheet(worksheet_name)

# 获得表头
def get_headers(worksheet):
    return worksheet.row_values(1)

# 获得表头下的内容
def get_column_by_header(worksheet, header_name):
    headers = get_headers(worksheet)
    col_index = headers.index(header_name) + 1  # +1 是因为gspread的索引是从1开始的
    return worksheet.col_values(col_index)

# 更新单元格的值
def update_cell(worksheet, header_name, row_number, value):
    headers = get_headers(worksheet)
    col_index = headers.index(header_name) + 1  # +1 是因为gspread的索引是从1开始的
    worksheet.update_cell(row_number, col_index, value)

# 将日期和时间转换为指定格式
def format_datetime(value):
    try:
        dt = datetime.datetime.strptime(value, '%d-%b-%Y %H:%M')
        return dt.strftime('%Y-%m-%d %H:%M')
    except ValueError:
        return ""

# 减少1小时
def subtract_hour(value):
    try:
        dt = datetime.datetime.strptime(value, '%Y-%m-%d %H:%M')
        dt -= datetime.timedelta(hours=1)
        return dt.strftime('%Y-%m-%d %H:%M')
    except ValueError:
        return ""

# 获取整个工作表的数据
def get_all_data(worksheet):
    return worksheet.get_all_values()

# 一次性更新整个工作表的数据
def update_all_data(worksheet, data):
    cell_range = f"A1:{gspread.utils.rowcol_to_a1(len(data), len(data[0]))}"
    cell_list = worksheet.range(cell_range)
    for i, row in enumerate(data):
        for j, value in enumerate(row):
            cell_list[i * len(row) + j].value = value
    worksheet.update_cells(cell_list)

# 只更新需要更新的部分
def update_changed_data(worksheet, old_data, new_data):
    changed_cells = []
    for i, (old_row, new_row) in enumerate(zip(old_data, new_data)):
        for j, (old_value, new_value) in enumerate(zip(old_row, new_row)):
            if old_value != new_value:
                cell = worksheet.cell(row=i+1, col=j+1)  # +1 because gspread is 1-indexed
                cell.value = new_value
                changed_cells.append(cell)
    if changed_cells:
        worksheet.update_cells(changed_cells, value_input_option='USER_ENTERED')

# 将格式化的日期时间字符串转换为datetime对象
def str_to_datetime(value):
    formats = ['%Y-%m-%d %H:%M', '%Y-%m-%d %H:%M']  # 添加其他可能的格式
    for fmt in formats:
        try:
            return datetime.datetime.strptime(value, fmt)
        except ValueError:
            continue
    return None

# 计算在不在21天内的数据
def is_date_within_21_days(date_str):
    try:
        # 将字符串转换为日期对象
        date_obj = datetime.datetime.strptime(date_str.strip(), "%d/%m/%Y %H:%M")
        today = datetime.datetime.now()
        # 计算日期和时间差
        delta = today - date_obj
        # 检查日期和时间差是否在-21到21天之间
        return timedelta(days=-21) <= delta <= timedelta(days=21)
    except ValueError:
        return False
