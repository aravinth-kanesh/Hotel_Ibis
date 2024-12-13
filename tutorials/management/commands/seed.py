from django.core.management.base import BaseCommand, CommandError

from tutorials.models import User, Tutor, Student, Language, StudentRequest, TutorAvailability, Message, Invoice, Lesson
from tutorials.term_dates import TERM_DATES, get_term
import random
from tutorials.models import User, Tutor, Student, Language, StudentRequest, TutorAvailability, Message, Invoice, Lesson
from tutorials.term_dates import TERM_DATES, get_term
import random
import pytz
from faker import Faker
from random import randint
from datetime import datetime, timedelta, time, date
from django.utils.timezone import now
from random import randint
from datetime import datetime, timedelta, time, date
from django.utils.timezone import now

user_fixtures = [
    {'username': '@johndoe', 'email': 'john.doe@example.org', 'first_name': 'John', 'last_name': 'Doe', 'role': 'admin'},
    {'username': '@janedoe', 'email': 'jane.doe@example.org', 'first_name': 'Jane', 'last_name': 'Doe', 'role': 'tutor'},
    {'username': '@charlie', 'email': 'charlie.johnson@example.org', 'first_name': 'Charlie', 'last_name': 'Johnson','role': 'student'},
]
language_fixtures = [
    {'name':'scala easy'},
    {'name':'python easy'},
    {'name':'c++ easy'},
    {'name':'java easy'},
    {'name':'django easy'},
    {'name':'kotlin easy'},
    
    {'name':'scala intermediate'},
    {'name':'python intermediate'},
    {'name':'c++ intermediate'},
    {'name':'java intermediate'},
    {'name':'django intermediate'},
    {'name':'kotlin intermediate'},
    
    {'name':'scala hard'},
    {'name':'python hard'},
    {'name':'c++ hard'},
    {'name':'java hard'},
    {'name':'django hard'},
    {'name':'kotlin hard'},    
]

message_fix = [
    {'recipient': lambda:User.objects.get(username='@charlie'), 
     'sender':lambda:User.objects.get(username='@janedoe'), 'subject':"Your new tutor" ,'content':"Hi Charlie, I'm your tutor."}
]


class Command(BaseCommand):
    """Build automation command to seed the database."""

    USER_COUNT = 300

    DEFAULT_PASSWORD = 'Password123'
    help = 'Seeds the database with sample data'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.faker = Faker('en_GB')

    def handle(self, *args, **options):

        self.create_lang()
        self.lang = Language.objects.all()
  
        self.create_users()
        self.users = User.objects.all()
        self.add_data()
        
        
    def create_lang(self):
        for data in language_fixtures:
            if not Language.objects.filter(name=data['name']).exists():
                Language.objects.get_or_create(name=data['name'])

    def create_users(self):
        self.generate_user_fixtures()
        self.generate_random_users()

    def generate_random_users(self):
        user_count = User.objects.count()
        while  user_count < self.USER_COUNT:
            print(f"Seeding user {user_count}/{self.USER_COUNT}", end='\r')
            self.generate_user()
            user_count = User.objects.count()
        print("User seeding complete.      ")

    def generate_user(self):
        first_name = self.faker.first_name()
        last_name = self.faker.last_name()
        email = create_email(first_name, last_name)
        username = create_username(first_name, last_name)
        role = weighted_random_role()
        self.try_create_user({'username': username, 'email': email, 'first_name': first_name, 'last_name': last_name, 'role': role})
        
       
    def try_create_user(self, data):
        try:
            self.create_user(data)
        except Exception as e:
            print(f"Failed to create user: {data['username']} - Error: {e}")
        

    def create_user(self, data):
        User.objects.create_user(
            username=data['username'],
            email=data['email'],
            password=Command.DEFAULT_PASSWORD,
            first_name=data['first_name'],
            last_name=data['last_name'],
            role=data['role']
        )
    def create_lesson(self, data):
        lesson = Lesson.objects.create(
            tutor=data['tutor'],
            student=data['student'],
            language=data['language'],
            price=data['price'],
            term=data['term'],
            frequency=data['frequency'],
            duration=data['duration'],
            venue=data['venue'],
            date=data['date'],
            time=data['time'],
        )
    
    def generate_lesson(self, tutor, student, language, date, term, end_date):
        venues = ["Library", "Cafe", "Zoom", "Student's Home", "School Classroom"]
        FREQUENCY_CHOICES = ['once a week', 'once per fortnight']
        durations = [30, 45, 60, 90, 120]

        price = randint(10, 40)
        frequency = random.choice(FREQUENCY_CHOICES)
        duration = random.choice(durations)
        venue = random.choice(venues)
        lesson_time = time(hour=random.randint(8, 20), minute=random.choice([0, 15, 30, 45]))
        current_date = date
        
        tutor.languages.add(language)
        self.create_tutor_availability(tutor,date,lesson_time)
        while current_date <= end_date:
            next_interval = 7 if frequency == 'once a week' else 14
            self.create_lesson({
                'tutor': tutor,
                'student': student,
                'language': language,
                'price': price,
                'term': term,
                'frequency': frequency,
                'duration': duration,
                'venue': venue,
                'date': current_date,
                'time': lesson_time,
            })
            current_date += timedelta(days= next_interval)
            
    def create_message(self,data):
        message = Message.objects.create(
            recipient=data['recipient'],
            sender=data['sender'],
            subject=data['subject'],
            content=data['content'],
        )
    def create_tutor_availability(self, tutor, current_date, start_time):
        
        if isinstance(current_date, datetime):
            current_date = current_date.date()
        term_info = get_term(current_date)
        end_date = term_info['end_date']
        
        while current_date <= end_date:
            if not TutorAvailability.objects.filter(
                        tutor=tutor,
                        day=current_date,
                        start_time=start_time,
                        end_time = time(23,0),
                        availability_status='available',
                            ).exists():
                    TutorAvailability.objects.create(
                        tutor=tutor,
                        day=current_date,
                        start_time=start_time,
                        end_time=time(23,0),
                        availability_status='available',
                    )
            current_date += timedelta(days=7)

            
            
        
    def generate_user_fixtures(self):
        for data in user_fixtures:
            self.try_create_user(data)
        tutor_user = User.objects.get(username='@janedoe')
        student_user = User.objects.get(username='@charlie')
        tutor, _  = Tutor.objects.get_or_create(UserID=tutor_user)[0]
        student = Student.objects.get_or_create(UserID=student_user)[0]
        lang = ['python hard', 'c++ easy', 'c++ intermediate']
        for l in lang:
            try:
                language = Language.objects.get(name=l)
                tutor.languages.add(language)
            except Language.DoesNotExist:
                print(f"Language '{l}' does not exist in the database.") 
        current_date = date(2025, 1, 10)
        start_time = time(15,0)
        self.create_tutor_availability(tutor,current_date,start_time)
        dates = get_term(current_date)
        term = dates['term']
        end_date = dates['end_date']
        language = Language.objects.get(name='python hard')
        
        self.generate_lesson(tutor, student, language, current_date, term, end_date)
        lesson = Lesson.objects.filter(student=student).first()
        StudentRequest.objects.create(
            student=student,
            language=language,
            description="Please help me with my Python.",
            date=current_date,
            time=lesson.time,
            venue=lesson.venue,
            duration=lesson.duration,
            frequency=lesson.frequency,
            term=term,
            is_allocated=True
        )
        invoice = self.create_invoice(student)
        invoice.paid = True
        invoice.date_paid = now().date()
        invoice.approved = True
        invoice.save()
        for data in message_fix:
            try:
                Message.objects.create(
                    recipient=data['recipient'](),
                    sender=data['sender'](),
                    subject=data['subject'],
                    content=data['content'],
                )
            except Exception as e:
                print(f"Failed to create message: {e}")

    def create_req(self, student, date, term):
        venues = ["Library", "Cafe", "Zoom", "Student's Home", "School Classroom"]
        descriptions = [
            "Focus on practical exercises.",
            "Prefer evening sessions.",
            "Need help with project.",
            "Timing is flexible."
        ]
        FREQUENCY_CHOICES = ['once a week', 'once per fortnight']
        durations = [30, 45, 60, 90, 120]

        StudentRequest.objects.create(
            student=student,
            language=random_language(),
            description=random.choice(descriptions),
            date=date,
            time=time(hour=random.randint(8, 20), minute=random.choice([0, 15, 30, 45])),
            venue=random.choice(venues),
            duration=random.choice(durations),
            frequency=random.choice(FREQUENCY_CHOICES),
            term=term,
        )
    def create_invoice(self,student):
        lessons = Lesson.objects.filter(student=student, invoice__isnull=True)
        if lessons.exists():
            total_amount = sum(lesson.price for lesson in lessons)
            tutor = lessons.first().tutor
            invoice = Invoice.objects.create(
                student=student,
                tutor=tutor,
                paid=False,
                total_amount = total_amount,
            )
            for lesson in lessons:
                lesson.invoice = invoice
                lesson.save()
            return invoice
        else:
            return None

            

    def add_data(self):
        for tutor in Tutor.objects.all():
            random_set_language(tutor)

        students = list(Student.objects.all())
        student_action = random.sample(students, 120)
        stages = ['request', 'invoice1', 'invoice2', 'invoice3', 'lesson']
        weights = [3, 2, 2, 1, 2]

        for student in student_action:
            s = random.choices(stages, weights=weights, k=1)[0]
            random_date_info = random_date(now().year)
            date, term = random_date_info['date'], random_date_info['term']
            tutor = Tutor.objects.order_by("?").first()
            language = Language.objects.order_by("?").first()

            if s == 'request':
                self.create_req(student, date, term)
            elif s in ['invoice1', 'invoice2', 'invoice3', 'lesson']:
                end_date = random_date_info['end_date']
                self.generate_lesson(tutor, student, language, date, term, end_date)
                lesson = Lesson.objects.filter(student=student).first()
                if lesson:
                    if s == 'invoice2':
                        self.create_invoice(student)
                    if s in 'invoice3':
                        invoice = self.create_invoice(student)
                        invoice.paid = True
                        invoice.date_paid = now().date()
                        invoice.save()
                    if s == 'lesson':
                        invoice = self.create_invoice(student)
                        invoice.paid = True
                        invoice.date_paid = now().date()
                        invoice.approved = True
                        invoice.save()        
def create_username(first_name, last_name):
    return '@' + first_name.lower() + last_name.lower()

def create_email(first_name, last_name):
    return first_name + '.' + last_name + '@example.org'

def weighted_random_role():
    roles = ['admin', 'tutor', 'student']
    weights = [1, 19, 40]  # 5 admin, 95 tutor, 200 students
    return random.choices(roles, weights=weights, k=1)[0]

def random_set_language(tutor):
    language_ids = list(Language.objects.values_list('id', flat=True))
    chosen_ids = random.sample(language_ids, random.randint(1, len(language_ids)/2))
    chosen_languages = Language.objects.filter(id__in=chosen_ids)
    tutor.languages.add(*chosen_languages)
    

def random_language():
    languages = list(Language.objects.all()) 
    if not languages:
        raise ValueError("No languages available in the database!")
    return random.choice(languages)
def random_date(year):
    date_ranges = []
    for term, dates in TERM_DATES.items():
        current_date = datetime(year, dates['start_date'][0], dates['start_date'][1])
        end_date = datetime(year, dates['end_date'][0], dates['end_date'][1])
        date_ranges.append((term, current_date, end_date))
    selected_term, current_date, end_date = random.choice(date_ranges)
    delta = end_date - current_date
    random_days = random.randint(0, delta.days)
    date = current_date + timedelta(days=random_days)
    
    
    return {
        'date': date,
        'term': selected_term,
        'end_date': end_date
    }
