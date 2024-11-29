import calendar
import datetime

def generate_calendar(year, month, events):
    cal = calendar.Calendar(firstweekday=6)  # Start week on Sunday
    month_days = cal.itermonthdates(year, month)

    weeks = []
    week = []

    # Organize events by date for quick lookup
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

class LessonCalendar(calendar.HTMLCalendar):
    def __init__(self, lessons, year, month):
        super().__init__()
        self.lessons = lessons  # dict: day (int) -> list of dicts with 'name' and 'time'
        self.year = year
        self.month = month

    def formatday(self, day, weekday):
        if day != 0:
            cssclass = self.cssclasses[weekday]
            # Highlight today's date
            if day == datetime.today().day and self.year == datetime.today().year and self.month == datetime.today().month:
                cssclass += ' today'
            lessons_html = ''
            for lesson in self.lessons.get(day, []):
                lessons_html += f'<div class="lesson-name">{lesson["time"]}: {lesson["name"]}</div>'
            return f'<td class="{cssclass}"><span class="date">{day}</span><div class="lessons">{lessons_html}</div></td>'
        return '<td class="noday">&nbsp;</td>'

    def formatweek(self, theweek):
        week_html = ''.join(self.formatday(d, wd) for (d, wd) in theweek)
        return f'<tr>{week_html}</tr>'

    def formatmonth(self, year, month, withyear=True):
        self.year, self.month = year, month
        return super().formatmonth(year, month, withyear)
