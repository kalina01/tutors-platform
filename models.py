import sqlite3 as db
from utils import DB_PATH, dict_factory


def create_group(group_name):
    with db.connect(DB_PATH) as conn:
        conn.execute("""
            insert into `group` (group_name)
            values (:group_name)
        """, {'group_name': group_name})


def create_student(FIO_student, telnumber_student):
    with db.connect(DB_PATH) as conn:
        conn.execute("""
            insert into student (FIO_student, telnumber_student)
            values (:FIO_student, :telnumber_student)
        """, {'FIO_student': FIO_student, 'telnumber_student': telnumber_student})


def get_students_for_admin():
    with db.connect(DB_PATH) as conn:
        conn.row_factory = db.Row
        cursor = conn.execute("""
            select distinct
                telnumber_student,
                FIO_student
            from student
            order by FIO_student
        """)
        return cursor.fetchall()


def create_course(
    name,
    room,
    start_date,
    week_amount,
    time,
    teacher_id,
    group_ids,
    days_of_week,
):
    time += ':00'
    with db.connect(DB_PATH) as conn:
        cursor = conn.execute("insert into course (name) values (:name)", {'name': name})
        course_id = cursor.lastrowid

        cursor = conn.execute("""
            insert into teacher_course (teacher_id, course_id)
            values (:teacher_id, :course_id)
        """, {'teacher_id': teacher_id, 'course_id': course_id})
        teacher_course_id = cursor.lastrowid

        course_start_schedule_ids = set()
        for group_id in group_ids:
            cursor = conn.execute("""
                insert into course_start_schedule
                (group_id, teacher_course_id, start_date, period, week_amount)
                values
                (:group_id, :teacher_course_id, :start_date, :period, :week_amount)
            """, {
                'group_id': group_id,
                'teacher_course_id': teacher_course_id,
                'start_date': start_date,
                'period': len(days_of_week),
                'week_amount': week_amount,
            })
            course_start_schedule_id = cursor.lastrowid
            course_start_schedule_ids.add(course_start_schedule_id)

            for day_id in days_of_week:
                conn.execute("""
                    insert into course_week (course_start_schedule_id, day_id)
                    values (:course_start_schedule_id, :day_id)
                """, {
                    'course_start_schedule_id': course_start_schedule_id,
                    'day_id': day_id,
                })

        for course_start_schedule_id in course_start_schedule_ids:
            conn.execute(f"""
                update class
                set
                    date = date || ' {time}',
                    room = :room
                where course_start_schedule_id = :course_start_schedule_id
            """, {
                'course_start_schedule_id': course_start_schedule_id,
                'room': room,
            })

        conn.commit()


def create_teacher(FIO_teacher, telnumber_teacher, password, is_admin=False):
    with db.connect(DB_PATH) as conn:
        conn.execute("""
            insert into teacher (FIO_teacher, telnumber_teacher, password, is_admin)
            values (:FIO_teacher, :telnumber_teacher, :password, :is_admin)
        """, {
            'FIO_teacher': FIO_teacher,
            'telnumber_teacher': telnumber_teacher,
            'password': password,
            'is_admin': is_admin,
        })
        conn.commit()


def get_courses():
    with db.connect(DB_PATH) as conn:
        conn.row_factory = db.Row
        cursor = conn.execute("""
            select
            	course_start_schedule_id,
            	id_course,
            	name,
            	FIO_teacher,
            	group_concat(distinct group_name) as `groups`,
            	start_date,
            	period * week_amount as lesson_amount,
            	room,
            	group_concat(distinct day_id) as days_of_week
            from course
            left join teacher_course on course.id_course = teacher_course.course_id
            left join teacher on teacher_course.teacher_id = teacher.id_teacher
            left join course_start_schedule using(teacher_course_id)
            left join `group` on course_start_schedule.group_id = `group`.id_group
            left join class using(course_start_schedule_id)
            left join course_week using(course_start_schedule_id)
            where start_date is not null
            group by course_start_schedule_id
            order by id_course desc
        """)
        return cursor.fetchall()


def create_teacher(FIO_teacher, telnumber_teacher, password, is_admin=False):
    with db.connect(DB_PATH) as conn:
        conn.execute("""
            insert into teacher (FIO_teacher, telnumber_teacher, password, is_admin)
            values (:FIO_teacher, :telnumber_teacher, :password, :is_admin)
        """, {
            'FIO_teacher': FIO_teacher,
            'telnumber_teacher': telnumber_teacher,
            'password': password,
            'is_admin': is_admin,
        })
        conn.commit()


def get_teachers_for_admin():
    with db.connect(DB_PATH) as conn:
        conn.row_factory = db.Row
        cursor = conn.execute("""
            select
                FIO_teacher,
                telnumber_teacher,
                is_admin,
                id_teacher
            from teacher
            order by FIO_teacher
        """)
        return cursor.fetchall()


def delete_student_from_group(student_id):
    with db.connect(DB_PATH) as conn:
        conn.execute("""
            delete from student where id_student = :student_id
        """, {'student_id': student_id})
        conn.commit()


def add_student_to_group(student_id, group_id):
    with db.connect(DB_PATH) as conn:
        cursor = conn.execute("""
            select FIO_student, telnumber_student
            from student
            where id_student = :student_id
        """, {'student_id': student_id})
        fio, tel = cursor.fetchone()
        conn.execute("""
            insert into student (group_id, FIO_student, telnumber_student)
            values (:group_id, :FIO_student, :telnumber_student)
        """, {'group_id': group_id, 'FIO_student': fio, 'telnumber_student': tel})
        conn.commit()


def get_students(exclude):
    with db.connect(DB_PATH) as conn:
        conn.row_factory = dict_factory
        cursor = conn.execute(f"""
            select
                FIO_student || ' (' || telnumber_student || ')' as student,
                id_student
            from student
            where telnumber_student not in (
                select telnumber_student from student
                where id_student in ({exclude})
            ) or {not exclude}
            group by FIO_student, telnumber_student
            order by student
        """)
        return cursor.fetchall()


def get_students_for_group(group_id):
    with db.connect(DB_PATH) as conn:
        conn.row_factory = db.Row
        cursor = conn.execute("""
            select
            	FIO_student,
            	telnumber_student,
            	id_student,
            	Sum(presence) as presence_count
            from student
            join attendance on attendance.student_id = student.id_student
            where group_id = :group_id
            group by id_student
        """, {'group_id': group_id})
        return cursor.fetchall()


def get_groups(teacher_id, all=False):
    with db.connect(DB_PATH) as conn:
        conn.row_factory = db.Row
        cursor = conn.execute("""
            select distinct id_group, group_name from `group`
            left join course_start_schedule on course_start_schedule.group_id = `group`.id_group
            left join teacher_course using(teacher_course_id)
            where teacher_id = :teacher_id or :all
        """, {'teacher_id': teacher_id, 'all': all})
        return cursor.fetchall()


def get_teachers():
    with db.connect(DB_PATH) as conn:
        conn.row_factory = db.Row
        cursor = conn.execute("""
            select id_teacher, FIO_teacher
            from teacher
            order by FIO_teacher
        """)
        return cursor.fetchall()


def set_attendance(attendance_list):
    with db.connect(DB_PATH) as conn:
        to_true = [obj['id'] for obj in attendance_list if obj['checked']]
        to_false = [obj['id'] for obj in attendance_list if not obj['checked']]
        sql = """
            update attendance
            set presence = %(presence)i
            where attendance_id in (%(attendance_ids)s)
        """
        conn.execute(sql % {'presence': 1, 'attendance_ids': ','.join(to_true)})
        conn.execute(sql % {'presence': 0, 'attendance_ids': ','.join(to_false)})
        conn.commit()


def get_students_for_class(class_id):
    with db.connect(DB_PATH) as conn:
        conn.row_factory = dict_factory
        cursor = conn.execute("""
            select
            	attendance_id,
            	presence,
            	FIO_student,
            	telnumber_student
            from attendance
            join student on student.id_student = attendance.student_id
            where class_id = :class_id
        """, {'class_id': class_id})
        return cursor.fetchall()


def get_class(class_id):
    with db.connect(DB_PATH) as conn:
        conn.row_factory = dict_factory
        cursor = conn.execute("""
            select
            	room,
            	`date`,
            	name,
            	group_id,
                FIO_teacher,
                group_name
            from class
            join course_start_schedule using(course_start_schedule_id)
            join teacher_course using(teacher_course_id)
            join course on teacher_course.course_id = course.id_course
            join teacher on teacher_course.teacher_id = teacher.id_teacher
            join `group` on `group`.id_group = course_start_schedule.group_id
            where class_id = :class_id
        """, {'class_id': class_id})
        return cursor.fetchone()


def get_schedule_list(teacher_id, from_day, to_day):
    from_day = str(from_day) + ' 00:00:00'
    to_day = str(to_day) + ' 23:59:59'
    with db.connect(DB_PATH) as conn:
        conn.row_factory = db.Row
        cursor = conn.execute("""
            select
            	class_id,
            	room,
            	`date`,
            	name,
            	group_id,
            	strftime('%w', `date`) as weekday,
                group_name
            from class
            join course_start_schedule using(course_start_schedule_id)
            join teacher_course using(teacher_course_id)
            join course on teacher_course.course_id = course.id_course
            join `group` on `group`.id_group = course_start_schedule.group_id
            where
            	teacher_id = :teacher_id
                and `date` between :from_day and :to_day
            order by `date` asc
        """, {'teacher_id': teacher_id, 'from_day': from_day, 'to_day': to_day})
        return cursor.fetchall()


def auth_user(tel, password):
    with db.connect(DB_PATH) as conn:
        conn.row_factory = db.Row
        cursor = conn.execute("""
            SELECT * FROM teacher
            WHERE telnumber_teacher = :tel
        """, {'tel': tel})
        user = cursor.fetchone()

    assert user is not None and user['password'] == password, 'Invalid phone number or password.'

    user = dict(user)
    del user['password']
    return user
