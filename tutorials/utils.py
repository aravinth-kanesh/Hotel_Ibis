import calendar
from datetime import datetime

# Makes a calendar for a specified year and month and adds events to the corresponding days.
def generate_calendar(year, month, events):
    cal = calendar.Calendar(firstweekday=6)  # Starts the week on Sunday.
    month_days = cal.itermonthdates(year, month)

    weeks = []
    week = []

    # Organises the events by date for quick lookup.
    events_by_date = {}
    for event in events:
        events_by_date.setdefault(event['date'], []).append(event)

    for day in month_days:
        day_events = events_by_date.get(day, [])
        day_dict = {
            'day': day,
            'events': day_events,
            'other_month': day.month != month,
        }
        week.append(day_dict)

        if len(week) == 7:
            weeks.append(week)
            week = []

    if week:
        weeks.append(week)

    return weeks

from calendar import HTMLCalendar
from datetime import date

# Makes a calendar that includes lessons for a specified month and year.
class LessonCalendar(HTMLCalendar):
    def __init__(self, lessons, year, month):
        super().__init__()
        self.lessons = self.group_by_day(lessons) # Groups the lessons by days.
        self.year = year
        self.month = month

    def group_by_day(self, lessons):
        """Groups lessons by their day."""
        lessons_by_day = {}
        for lesson in lessons:
            day = lesson.date.day
            lessons_by_day.setdefault(day, []).append(lesson)
        return lessons_by_day

    def formatday(self, day, weekday):
        """Formats a day as a table cell."""
        if day == 0:
            return '<td class="noday">&nbsp;</td>'  # Blank day

        cssclass = self.cssclasses[weekday]
        if date.today() == date(self.year, self.month, day):
            cssclass += ' today'

        day_html = f'<span class="date">{day}</span>'
        lesson_html = ''

        if day in self.lessons:
            # Add lessons to the day's HTML
            lesson_list = ''.join(
                f'<div class="lesson">{lesson.language.name} at {lesson.time}</div>'
                for lesson in self.lessons[day]
            )
            lesson_html = f'<div class="lessons">{lesson_list}</div>'

        return f'<td class="{cssclass}">{day_html}{lesson_html}</td>'

    def formatmonth(self, year, month, withyear=True):
        """Formats a month as a table."""
        self.year, self.month = year, month
        return super().formatmonth(year, month, withyear)
