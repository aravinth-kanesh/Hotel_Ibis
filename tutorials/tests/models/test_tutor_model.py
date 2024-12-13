from django.test import TestCase
from tutorials.models import Tutor, User, Language

class TutorModelTest(TestCase):
    """Test suite for the Tutor model."""

    def setUp(self):
        self.user1 = User.objects.create(username="tutorone", first_name="John", last_name="Doe", email="john@example.com")
        self.user2 = User.objects.create(username="tutortwo", first_name="Jane", last_name="Smith", email="jane@example.com")
        self.user3 = User.objects.create(username="tutorthree", first_name="Alice", last_name="Johnson", email="alice@example.com")

        self.language_java = Language.objects.create(name="java")
        self.language_python = Language.objects.create(name="python")
        self.language_cplusplus = Language.objects.create(name="c++")
        self.language_scala = Language.objects.create(name="scala")
        self.language_javascript = Language.objects.create(name="javascript")

        self.tutor1 = Tutor.objects.create(UserID=self.user1)  
        self.tutor2 = Tutor.objects.create(UserID=self.user2)  
        self.tutor3 = Tutor.objects.create(UserID=self.user3)  

        self.tutor1.languages.add(self.language_java, self.language_python)
        self.tutor2.languages.add(self.language_cplusplus)
        self.tutor3.languages.add(self.language_scala, self.language_javascript)

    def test_tutor_string_representation(self):
        """Test the __str__ method of the Tutor model."""
        expected_str1 = "John Doe"
        expected_str2 = "Jane Smith"
        expected_str3 = "Alice Johnson"

        self.assertEqual(str(self.tutor1), expected_str1)
        self.assertEqual(str(self.tutor2), expected_str2)
        self.assertEqual(str(self.tutor3), expected_str3)

    def test_user_deletion_cascades_to_tutor(self):
        """Test that deleting a user also deletes the associated tutor."""
        self.tutor3.delete()
        self.user3.delete()
        
        with self.assertRaises(Tutor.DoesNotExist):
            Tutor.objects.get(UserID=self.user3.id)

    def test_language_assignment(self):
        """Test that programming languages are correctly assigned to tutors."""
        self.assertQuerySetEqual(
            self.tutor1.languages.order_by("name"),
            [self.language_java, self.language_python],
            transform=lambda x: x
        )
        self.assertQuerySetEqual(
            self.tutor2.languages.order_by("name"),
            [self.language_cplusplus],
            transform=lambda x: x
        )
        self.assertCountEqual(
            self.tutor3.languages.all(),
            [self.language_scala, self.language_javascript]
        )

    def test_remove_language(self):
        """Test removing a language from a tutor."""
        self.tutor1.languages.remove(self.language_java)
        self.assertQuerySetEqual(
            self.tutor1.languages.order_by("name"),
            [self.language_python],
            transform=lambda x: x
        )

    def test_clear_languages(self):
        """Test clearing all languages from a tutor."""
        self.tutor1.languages.clear()
        self.assertQuerySetEqual(
            self.tutor1.languages.all(),
            [],
            transform=lambda x: x
        )

    def test_delete_language(self):
        """Test behavior when a language is deleted."""
        self.language_java.delete()
        self.assertQuerySetEqual(
            self.tutor1.languages.all(),
            [self.language_python],
            transform=lambda x: x
        )

    def test_language_querying(self):
        """Test querying tutors by languages they teach."""
        tutors = Tutor.objects.filter(languages__name="java")
        self.assertQuerySetEqual(
            tutors,
            [self.tutor1],
            transform=lambda x: x
        )

    def test_no_language_assignment(self):
        """Test the string representation of a tutor with no languages."""
        self.tutor2.languages.clear()
        expected_str = "Jane Smith"
        self.assertEqual(str(self.tutor2), expected_str)

    def test_duplicate_language_assignment(self):
        """Test assigning the same language multiple times."""
        self.tutor1.languages.add(self.language_python)
        self.assertQuerySetEqual(
            self.tutor1.languages.order_by("name"),
            [self.language_java, self.language_python],
            transform=lambda x: x
        )

    def test_query_tutors_by_multiple_languages(self):
        """Test querying tutors by multiple languages."""
        # Add an additional language
        self.language_c = Language.objects.create(name="c")
        self.tutor1.languages.add(self.language_c)

        tutors = Tutor.objects.filter(languages__name__in=["java", "python", "c"]).distinct()
        self.assertQuerySetEqual(
            tutors.order_by("id"),
            [self.tutor1],
            transform=lambda x: x
        )

    def test_edge_case_empty_languages(self):
        """Test behavior when tutors have no languages assigned."""
        self.tutor3.languages.clear()
        self.assertEqual(self.tutor3.languages.count(), 0)

    def test_partial_match_query(self):
        """Test partial match query logic for filtering tutors by language names."""
        # Add an additional language
        self.language_german = Language.objects.create(name="german")
        self.tutor1.languages.add(self.language_german)
        
        tutors = Tutor.objects.filter(languages__name__icontains="ger")
        self.assertQuerySetEqual(
            tutors.order_by("id"),
            [self.tutor1],
            transform=lambda x: x
        )

    def test_no_languages_edge_case(self):
        """Test string representation for tutors with absolutely no languages."""
        self.tutor1.languages.clear()
        self.assertEqual(str(self.tutor1), "John Doe")