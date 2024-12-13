import unittest
from datetime import date, datetime, timedelta
from calendar import HTMLCalendar
from tutorials.utils import generate_calendar, LessonCalendar

class TestGenerateCalendar(unittest.TestCase):
    def test_generate_calendar_basic(self):
        year, month = 2023, 10
        events = [
            {'date': date(2023, 10, 5), 'name': 'Event 1'},
            {'date': date(2023, 10, 12), 'name': 'Event 2'},
        ]

        weeks = generate_calendar(year, month, events)

        # Check number of weeks
        self.assertGreaterEqual(len(weeks), 4)
        self.assertLessEqual(len(weeks), 6)

        # Check event assignment
        for week in weeks:
            for day in week:
                if day['day'] == date(2023, 10, 5):
                    self.assertEqual(len(day['events']), 1)
                    self.assertEqual(day['events'][0]['name'], 'Event 1')

                if day['day'] == date(2023, 10, 12):
                    self.assertEqual(len(day['events']), 1)
                    self.assertEqual(day['events'][0]['name'], 'Event 2')

    def test_generate_calendar_with_cross_month(self):
        year, month = 2023, 1
        events = []  # No events

        weeks = generate_calendar(year, month, events)

        # Check that days from previous or next month are marked correctly
        for week in weeks:
            for day in week:
                if day['day'].month != month:
                    self.assertTrue(day['other_month'])


class MockLesson:
    def __init__(self, date, language, time):
        self.date = date
        self.language = type('Language', (object,), {'name': language})
        self.time = time

class TestLessonCalendar(unittest.TestCase):
    def test_group_by_day(self):
        lessons = [
            MockLesson(date(2023, 10, 5), 'Python', '10:00 AM'),
            MockLesson(date(2023, 10, 5), 'Java', '2:00 PM'),
            MockLesson(date(2023, 10, 12), 'C++', '3:00 PM'),
        ]

        calendar = LessonCalendar(lessons, 2023, 10)

        grouped = calendar.group_by_day(lessons)

        self.assertEqual(len(grouped), 2)
        self.assertEqual(len(grouped[5]), 2)
        self.assertEqual(len(grouped[12]), 1)

    def test_formatday(self):
        lessons = [
            MockLesson(date(2023, 10, 5), 'Python', '10:00 AM'),
        ]

        calendar = LessonCalendar(lessons, 2023, 10)
        formatted_day = calendar.formatday(5, 0)

        self.assertIn('Python at 10:00 AM', formatted_day)
        self.assertIn('<td class="mon">', formatted_day)

    def test_formatmonth(self):
        lessons = [
            MockLesson(date(2023, 10, 5), 'Python', '10:00 AM'),
            MockLesson(date(2023, 10, 12), 'Java', '2:00 PM'),
        ]

        calendar = LessonCalendar(lessons, 2023, 10)
        formatted_month = calendar.formatmonth(2023, 10)

        self.assertIn('<table', formatted_month)
        self.assertIn('Python at 10:00 AM', formatted_month)
        self.assertIn('Java at 2:00 PM', formatted_month)

if __name__ == "__main__":
    unittest.main()
