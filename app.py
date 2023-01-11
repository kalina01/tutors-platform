import os
import locale
from flask import Flask


locale.setlocale(locale.LC_ALL, '')
app = Flask(__name__)
app.secret_key = bytes(os.getenv('SECRET_KEY', 'unsafe_default'), encoding='utf-8')


from controllers import (
    add_student_to_group,
    all_students,
    groups,
    check_attendance,
    schedule_detail,
    schedule_list,
    index,
    login,
    logout,
)
