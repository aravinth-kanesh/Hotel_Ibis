from django.core.management.base import BaseCommand, CommandError

from tutorials.models import User

import pytz
from faker import Faker
from random import randint, random

# sample user fixture data
user_fixtures = [
    {'username': '@johndoe', 'email': 'john.doe@example.org', 'first_name': 'John', 'last_name': 'Doe'},
    {'username': '@janedoe', 'email': 'jane.doe@example.org', 'first_name': 'Jane', 'last_name': 'Doe'},
    {'username': '@charlie', 'email': 'charlie.johnson@example.org', 'first_name': 'Charlie', 'last_name': 'Johnson'},
]


class Command(BaseCommand):
    """Build automation command to seed the database."""

    USER_COUNT = 300
    DEFAULT_PASSWORD = 'Password123' 
    help = 'Seeds the database with sample data'

    def __init__(self, *args, **kwargs):
        """ initialises command and sets up faker instance """
        super().__init__(*args, **kwargs)
        self.faker = Faker('en_GB')

    def handle(self, *args, **options):
        """ main entry point for command execution """
        self.create_users()
        self.users = User.objects.all()

    def create_users(self):
        """ user creation process """
        self.generate_user_fixtures()
        self.generate_random_users()

    def generate_user_fixtures(self):
        """ creates users on fixture data """
        for data in user_fixtures:
            self.try_create_user(data)

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
        self.try_create_user({'username': username, 'email': email, 'first_name': first_name, 'last_name': last_name})
       
    def try_create_user(self, data):
        """ ignores errors to try to create user """
        try:
            self.create_user(data)
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
        )

def create_username(first_name, last_name):
    """ makes full name as username """
    return '@' + first_name.lower() + last_name.lower()

def create_email(first_name, last_name):
    return first_name + '.' + last_name + '@example.org'
