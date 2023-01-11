from calendar import day_abbr
from datetime import datetime, timedelta
from urllib import request
from flask import render_template, request, redirect, session
from app import app
from utils import login_required, admin_only
import models as m


@app.route('/groups/create', methods=['GET', 'POST'])
@admin_only
def create_group(user):
    if request.method == 'POST':
        m.create_group(**request.values)
        return redirect('/groups')

    return render_template(
        'create_group.j2'
    )


@app.route('/students/create', methods=['GET', 'POST'])
@admin_only
def create_student(user):
    if request.method == 'POST':
        m.create_student(**request.values)
        return redirect('/students')

    return render_template(
        'create_student.j2'
    )


@app.route('/students')
@admin_only
def students(user):
    return render_template(
        'students.j2',
        students=m.get_students_for_admin()
    )


@app.route('/courses/create', methods=['GET', 'POST'])
@admin_only
def create_course(user):
    if request.method == 'POST':
        req = dict(request.values)
        req['group_ids'] = request.values.getlist('group_ids')
        req['days_of_week'] = sorted([int(d) for d in request.values.getlist('days_of_week')])
        m.create_course(**req)
        return redirect('/courses')

    return render_template(
        'create_course.j2',
        groups=m.get_groups(user['id_teacher'], all=True),
        teachers=m.get_teachers_for_admin(),
    )


@app.route('/courses')
@admin_only
def courses(user):
    return render_template(
        'courses.j2',
        courses=m.get_courses(),
        strptime=datetime.strptime,
        day_abbr=day_abbr,
        int=int,
        enumerate=enumerate,
        len=len,
    )


@app.route('/teachers/create', methods=['GET', 'POST'])
@admin_only
def create_teacher(user):
    if request.method == 'POST':
        m.create_teacher(**request.values)
        return redirect('/teachers')

    return render_template(
        'create_teacher.j2'
    )


@app.route('/teachers')
@admin_only
def teachers(user):
    return render_template(
        'teachers.j2',
        teachers=m.get_teachers_for_admin()
    )


@app.route('/delete_student_from_group', methods=['POST'])
@login_required
def delete_student_from_group(user):
    m.delete_student_from_group(request.json['student_id'])
    return {'OK': True}


@app.route('/add_student_to_group', methods=['POST'])
@login_required
def add_student_to_group(user):
    m.add_student_to_group(request.json['student_id'], request.json['group_id'])
    return {'OK': True}


@app.route('/all_students')
@login_required
def all_students(user):
    exclude = request.values.get('exclude', '');
    return {'students': m.get_students(exclude)}


@app.route('/groups')
@login_required
def groups(user):
    teacher_id = request.values.get('teacher_id', user['id_teacher'])
    groups = m.get_groups(teacher_id, all=bool(user['is_admin']))
    first_group_id = groups[0]['id_group'] if groups else 0
    group_id = request.values.get('group_id', first_group_id)
    return render_template(
        'groups.j2',
        groups=groups,
        students=m.get_students_for_group(group_id),
        int=int,
        enumerate=enumerate,
    )


@app.route('/check_attendance', methods=['POST'])
@login_required
def check_attendance(user):
    m.set_attendance(request.json)
    return {'OK': True}


@app.route('/schedule/<int:class_id>')
@login_required
def schedule_detail(class_id, user):
    return {
        'class': m.get_class(class_id),
        'students': m.get_students_for_class(class_id),
    }


@app.route('/schedule')
@login_required
def schedule_list(user):
    date_string = request.values.get('date')
    date = datetime.now()
    if date_string:
        date = datetime.strptime(date_string, '%Y-%m-%d')
    monday = (date - timedelta(days=date.weekday())).date()
    saturday = monday + timedelta(days=6)
    teacher_id = request.values.get('teacher_id', user['id_teacher'])
    return render_template(
        'schedule.j2',
        data=m.get_schedule_list(teacher_id, from_day=monday, to_day=saturday),
        monday=monday,
        saturday=saturday,
        range=range,
        int=int,
        strptime=datetime.strptime,
        timedelta=timedelta,
        teachers=m.get_teachers(),
        now=datetime.now,
        list=list,
    )


@app.route('/')
def index():
    return redirect('/schedule')


@app.route('/login', methods=['GET', 'POST'])
def login():
    message = None

    if request.method == 'POST':
        try:
            user = m.auth_user(request.values.get('tel'), request.values.get('password'))
            session['user'] = user
            return redirect(request.values.get('next', '/'))
        except AssertionError as error:
            message = error.args[0]

    return render_template('login.j2', message=message)


@app.route('/logout', methods=['GET'])
def logout():
    session['user'] = None
    return redirect('/')
