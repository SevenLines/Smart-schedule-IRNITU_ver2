import os
import calendar
from datetime import datetime, date

import dotenv
import pendulum as pendulum

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from db.models.postgres_models import Vacpara, RealGroup, Prepod, Auditorie, DisciplineDB, \
    ScheduleMetaprogramDiscipline, ScheduleV2
from db.models.response_models import LessonsTime, Institute, Group, Teacher, Classroom, Discipline, OtherDiscipline, \
    Schedule

dotenv.load_dotenv()

PG_DB_DATABASE = os.environ.get('PG_DB_DATABASE', default='schedule')
PG_DB_USER = os.environ.get('PG_DB_USER')
PG_DB_PASSWORD = os.environ.get('PG_DB_PASSWORD')
PG_DB_HOST = os.environ.get('PG_DB_HOST')
PG_DB_PORT = os.environ.get('PG_DB_PORT', default='5432')

POSTGRES_DATABASE = f"postgresql+psycopg2://{PG_DB_USER}:{PG_DB_PASSWORD}@{PG_DB_HOST}:{PG_DB_PORT}/{PG_DB_DATABASE}"

engine = create_engine(POSTGRES_DATABASE, echo=True)


def is_even_week(start_date: date):
    september_1st = datetime(start_date.year, 9, 1)

    if start_date.month >= 9 or start_date.isocalendar()[1] == september_1st.isocalendar()[1]:
        september_1st = datetime(start_date.year, 9, 1)
    else:
        september_1st = datetime(start_date.year - 1, 9, 1)

    if isinstance(start_date, date):
        start_date = datetime.combine(start_date, datetime.min.time())

    start_date = pendulum.instance(start_date)
    study_year_start = pendulum.instance(september_1st).start_of("week")
    weeks = (start_date - study_year_start).days // 7

    return weeks % 2 == 1


def get_lessons_time() -> list:
    with Session(engine) as session:
        lessons_time = session.query(Vacpara)\
            .order_by(Vacpara.id_66)\
            .all()

        return [LessonsTime(lt) for lt in lessons_time]


def get_institutes() -> list:
    with Session(engine) as session:
        institutes = session.query(RealGroup) \
            .distinct(RealGroup.faculty_title)\
            .where(RealGroup.faculty_title != '') \
            .all()

        return sorted([Institute(i) for i in institutes], key=lambda i: i.institute_id)


def get_groups() -> list:
    with Session(engine) as session:
        groups = session.query(RealGroup)\
            .where(RealGroup.is_active == True)\
            .order_by(RealGroup.id_7)\
            .all()

        return [Group(g) for g in groups]


def get_teachers() -> list:
    with Session(engine) as session:
        teachers = session.query(Prepod)\
            .where(Prepod.preps != '')\
            .order_by(Prepod.id_61)\
            .all()

        return [Teacher(t) for t in teachers]


def get_classrooms() -> list:
    with Session(engine) as session:
        classrooms = session.query(Auditorie)\
            .where(Auditorie.obozn != '' and Auditorie.obozn != '-') \
            .order_by(Auditorie.id_60).all()

        return [Classroom(c) for c in classrooms]


def get_disciplines() -> list:
    with Session(engine) as session:
        disciplines = session.query(DisciplineDB)\
            .where(DisciplineDB.title != '')\
            .order_by(DisciplineDB.id)\
            .all()

        return [Discipline(d) for d in disciplines]


def get_other_disciplines() -> list:
    with Session(engine) as session:
        other_disciplines = session.query(ScheduleMetaprogramDiscipline) \
            .where(ScheduleMetaprogramDiscipline.is_active == True and
                   ScheduleMetaprogramDiscipline.project_active == True) \
            .order_by(ScheduleMetaprogramDiscipline.id)\
            .all()

        return [OtherDiscipline(od) for od in other_disciplines]


def get_schedule(start_date: datetime) -> list:
    start_of_first_week = pendulum.instance(start_date).start_of("week")
    start_of_second_week = pendulum.instance(start_of_first_week).add(weeks=1)

    with Session(engine) as session:
        schedules = session.query(ScheduleV2) \
            .where(start_of_first_week.date() <= ScheduleV2.dbeg) \
            .where(ScheduleV2.dbeg <= start_of_second_week.date()) \
            .order_by(ScheduleV2.id)\
            .all()

        schedules = list(filter(lambda s: (s.everyweek == 2 or s.everyweek == 1 and s.day > 7) if is_even_week(s.dbeg)
                else (s.everyweek == 2 or s.everyweek == 1 and s.day <= 7), schedules))

        return [Schedule(s) for s in schedules]


def get_schedule_month(year: int, month: int) -> list:
    start_day_of_month = date(year, month, 1)
    end_day_of_month = date(year, month, calendar.monthrange(year, month)[1])

    with Session(engine) as session:
        schedules = session.query(ScheduleV2) \
            .where(start_day_of_month <= ScheduleV2.dbeg) \
            .where(ScheduleV2.dbeg <= end_day_of_month) \
            .order_by(ScheduleV2.id)\
            .all()

        schedules = list(filter(lambda s: (s.everyweek == 2 or s.everyweek == 1 and s.day > 7) if is_even_week(s.dbeg)
                else (s.everyweek == 2 or s.everyweek == 1 and s.day <= 7), schedules))

        return [Schedule(s) for s in schedules]
