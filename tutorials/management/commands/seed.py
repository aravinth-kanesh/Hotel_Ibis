from django.core.management.base import BaseCommand, CommandError

from tutorials.models import User
from tutorials.models import Tutor
from tutorials.models import Language

import pytz
from faker import Faker
from random import randint, choice

# sample user fixture data
user_fixtures = [
    {'username': '@johndoe', 'email': 'john.doe@example.org', 'first_name': 'John', 'last_name': 'Doe', 'role': 'admin'},
    {'username': '@janedoe', 'email': 'jane.doe@example.org', 'first_name': 'Jane', 'last_name': 'Doe', 'role' : 'tutor'},
    {'username': '@charlie', 'email': 'charlie.johnson@example.org', 'first_name': 'Charlie', 'last_name': 'Johnson', 'role': 'student'},
]

tutor_fixtures = [
    {'username': '@janedoe'}
]


class Command(BaseCommand):
    """Build automation command to seed the database."""

    USER_COUNT = 300
    DEFAULT_PASSWORD = 'Password123'
    ROLE_CHOICES = ['admin', 'tutor', 'student']
    LANGUAGE_CHOICES = ['c++', 'Java', 'Python', 'Scala']
    help = 'Seeds the database with sample data'

    def __init__(self, *args, **kwargs):
        """ initialises command and sets up faker instance """
        super().__init__(*args, **kwargs)
        self.faker = Faker('en_GB')

    def handle(self, *args, **options):
        """ main entry point for command execution """
        self.create_lang()
        self.create_users()
        self.users = User.objects.all()

    def create_lang(self):
        for lang in self.LANGUAGE_CHOICES:
            Language.objects.get_or_create(name=lang)

    def create_users(self):
        """ user creation process """
        self.generate_user_fixtures()
        self.generate_tutor_fixtures()
        self.generate_random_users()

    def generate_user_fixtures(self):
        """ creates users on fixture data """
        for data in user_fixtures:
            self.try_create_user(data)

    def generate_tutor_fixtures(self):
        for data in tutor_fixtures:
            user = User.objects.get(username=data['username'])
            self.create_tutor(user)

    def generate_random_users(self):
        """ generates random users till until target count """
        user_count = User.objects.count()
        while  user_count < self.USER_COUNT:
            print(f"Seeding user {user_count}/{self.USER_COUNT}", end='\r')
            self.generate_user()
            user_count = User.objects.count()
        print("User seeding complete.      ")

    def generate_user(self):
        """ generates random user using faker """
        first_name = self.faker.first_name()
        last_name = self.faker.last_name()
        email = create_email(first_name, last_name)
        username = create_username(first_name, last_name)
        role = choice(self.ROLE_CHOICES)
        self.stdout.write(self.style.SUCCESS(f"Generated user with role: {role}"))
        user = self.try_create_user({'username': username, 'email': email, 'first_name': first_name, 'last_name': last_name, 'role': role})
        if role == 'tutor':
            self.create_tutor(user)
        
    def try_create_user(self, data):
        """ ignores errors to try to create user """
        try:
            return self.create_user(data)
        except:
            pass

    def create_user(self, data):
        """ creates user """
        User.objects.create_user(
            username=data['username'],
            email=data['email'],
            password=Command.DEFAULT_PASSWORD,
            first_name=data['first_name'],
            last_name=data['last_name'],
            role=data['role']
        )
    
    def generate_languages(self):
        languages = set()
        while len(languages) < 2:
            languages.add(choice(self.LANGUAGE_CHOICES))
        return list(languages)
    
    def create_tutor(self, user):
        if user.role == 'tutor':
            languages_queryset = Language.objects.all()
            random_language = choice(list(languages_queryset))

        # Create a Tutor instance and associate it with the user
            tutor = Tutor.objects.create(UserID=user)
            tutor.languages.add(random_language)
            tutor.save()

            print(f"Tutor created for {user.username} with languages: {', '.join(lang.name for lang in tutor.languages.all())}")
        else:
            print(f"User {user.username} is not a tutor, skipping tutor creation.")
        
def create_username(first_name, last_name):
    """ makes full name as username """
    return '@' + first_name.lower() + last_name.lower()

def create_email(first_name, last_name):
    return first_name + '.' + last_name + '@example.org'
