import os

# 配置JSON文件
current_script_path = os.path.dirname(os.path.abspath(__file__))
relative_path = os.path.join('..', 'tools', 'vic-depot-95801651e707.json')
json_file_path = os.path.abspath(os.path.join(current_script_path, relative_path))

# 配置通信方法
SCOPE = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/spreadsheets",
         "https://www.googleapis.com/auth/drive.file", "https://www.googleapis.com/auth/drive"]

