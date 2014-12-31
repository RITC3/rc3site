from models import Semester

CURRENT_SEMESTER = Semester.query.filter_by(current=True).first()
SEMESTERS = Semester.query.all()
