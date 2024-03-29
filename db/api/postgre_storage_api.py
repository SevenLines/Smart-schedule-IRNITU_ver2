import calendar
import os
from datetime import datetime, date

import dotenv
import pendulum
from sqlalchemy import create_engine, func, cast, Numeric
from sqlalchemy.orm import Session

from db.models.postgres_models import Vacpara, RealGroup, Prepod, Auditorie, DisciplineDB, \
    ScheduleMetaprogramDiscipline, ScheduleV2, QueryDB
from db.models.response_models import LessonsTime, Institute, Group, Teacher, Classroom, Discipline, OtherDiscipline, \
    Schedule, Query

dotenv.load_dotenv()

PG_DB_DATABASE = os.environ.get('PG_DB_DATABASE', default='schedule')
PG_DB_USER = os.environ.get('PG_DB_USER')
PG_DB_PASSWORD = os.environ.get('PG_DB_PASSWORD')
PG_DB_HOST = os.environ.get('PG_DB_HOST')
PG_DB_PORT = os.environ.get('PG_DB_PORT', default='5432')

POSTGRES_DATABASE = f"postgresql+psycopg2://{PG_DB_USER}:{PG_DB_PASSWORD}@{PG_DB_HOST}:{PG_DB_PORT}/{PG_DB_DATABASE}"

engine = create_engine(POSTGRES_DATABASE, echo=True)


def get_start_date_of_study_year(study_date: date) -> datetime:
    september_first = datetime(study_date.year, 9, 1)

    if study_date.month >= 9 or study_date.isocalendar()[1] == september_first.isocalendar()[1]:
        september_first = datetime(study_date.year, 9, 1)
    else:
        september_first = datetime(study_date.year - 1, 9, 1)

    return datetime.fromisoformat(pendulum.instance(september_first).start_of("week").to_datetime_string())


def get_lessons_time() -> list:
    with Session(engine) as session:
        lessons_time = session.query(Vacpara) \
            .order_by(Vacpara.id_66) \
            .all()

        return [LessonsTime(lt) for lt in lessons_time]


def get_institutes() -> list:
    with Session(engine) as session:
        institutes = session.query(RealGroup) \
            .distinct(RealGroup.faculty_title) \
            .where(RealGroup.faculty_title != '') \
            .all()

        return sorted([Institute(i) for i in institutes], key=lambda i: i.institute_id)


def get_groups() -> list:
    with Session(engine) as session:
        groups = session.query(RealGroup) \
            .order_by(RealGroup.id_7) \
            .all()

        return [Group(g) for g in groups]


def get_teachers() -> list:
    with Session(engine) as session:
        teachers = session.query(Prepod) \
            .where(Prepod.preps != '') \
            .order_by(Prepod.id_61) \
            .all()

        return [Teacher(t) for t in teachers]


def get_classrooms() -> list:
    with Session(engine) as session:
        classrooms = session.query(Auditorie) \
            .where((Auditorie.obozn != '') & (Auditorie.obozn != '-')) \
            .order_by(Auditorie.id_60).all()

        return [Classroom(c) for c in classrooms]


def get_disciplines() -> list:
    with Session(engine) as session:
        disciplines = session.query(DisciplineDB) \
            .where(DisciplineDB.title != '') \
            .order_by(DisciplineDB.id) \
            .all()

        return [Discipline(d) for d in disciplines]


def get_other_disciplines() -> list:
    with Session(engine) as session:
        other_disciplines = session.query(ScheduleMetaprogramDiscipline) \
            .order_by(ScheduleMetaprogramDiscipline.id) \
            .all()

        return [OtherDiscipline(od) for od in other_disciplines]


def get_queries() -> list:
    with Session(engine) as session:
        queries = session.query(QueryDB) \
            .order_by(QueryDB.id) \
            .all()

        return [Query(q) for q in queries]


def get_schedule(start_date: datetime) -> list:
    start_of_first_week = pendulum.instance(start_date).start_of("week")
    start_of_second_week = pendulum.instance(start_of_first_week).add(weeks=1).date()
    start_of_first_week = start_of_first_week.date()

    start_date_of_study_year = get_start_date_of_study_year(start_date)

    return extract_schedule(start_date_of_study_year, start_of_first_week, start_of_second_week)


def get_schedule_month(year: int, month: int) -> list:
    start_day_of_month = pendulum.instance(datetime(year, month, 1)).start_of("week")
    end_day_of_month = date(year, month, calendar.monthrange(year, month)[1])
    start_date_of_study_year = get_start_date_of_study_year(datetime(year, month, end_day_of_month.day))

    return extract_schedule(start_date_of_study_year, start_day_of_month, end_day_of_month)


def extract_schedule(start_date_of_study_year, start_date, end_date):
    with Session(engine) as session:
        difference_of_weeks = cast(
            func.trunc(
                func.date_part(
                    'day',
                    ScheduleV2.dbeg - start_date_of_study_year
                ) / 7
            ), Numeric)

        schedules = session.query(ScheduleV2) \
            .where((start_date <= ScheduleV2.dbeg) & (ScheduleV2.dbeg <= end_date)) \
            .where((ScheduleV2.everyweek == 2) |
                   ((ScheduleV2.everyweek == 1) & (ScheduleV2.day > 7) & (difference_of_weeks % 2 == 1)) |
                   ((ScheduleV2.everyweek == 1) & (ScheduleV2.day <= 7) & (difference_of_weeks % 2 == 0))) \
            .order_by(ScheduleV2.id) \
            .all()

        return [Schedule(s) for s in schedules]
