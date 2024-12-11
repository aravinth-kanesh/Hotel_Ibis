from django.test import TestCase
from tutorials.models import Language

class LanguageModelTest(TestCase):
    """Test suite for the Language model."""

    def setUp(self):
        """Set up initial test data."""
        self.language_java = Language.objects.create(name="java")
        self.language_python = Language.objects.create(name="python")
        self.language_cplusplus = Language.objects.create(name="C++")

    def test_language_string_representation(self):
        """Test the __str__ method of the Language model."""
        self.assertEqual(str(self.language_java), "Java")
        self.assertEqual(str(self.language_python), "Python")
        self.assertEqual(str(self.language_cplusplus), "C++")

    def test_language_name_normalization(self):
        """Test that the name is normalized to lowercase before saving."""
        language = Language.objects.create(name="JAVASCRIPT")
        self.assertEqual(language.name, "javascript")
        self.assertEqual(str(language), "Javascript")

    def test_unique_language_name(self):
        """Test that language names must be unique."""
        with self.assertRaises(Exception):
            Language.objects.create(name="java")  # Duplicate name

    def test_max_length_validation(self):
        """Test that the name field enforces its max length."""
        long_name = "x" * 101
        language = Language(name=long_name)
        with self.assertRaises(Exception):
            language.save()

    def test_title_case_string_representation(self):
        """Test that string representation is always in title case."""
        language = Language.objects.create(name="RuBy")
        self.assertEqual(str(language), "Ruby")

    def test_save_method_override(self):
        """Test the custom save method for name normalization."""
        language = Language.objects.create(name="Swift")
        self.assertEqual(language.name, "swift")
        self.assertEqual(str(language), "Swift")

    def test_case_insensitivity_for_uniqueness(self):
        """Test that uniqueness is case insensitive."""
        with self.assertRaises(Exception):
            Language.objects.create(name="Python")  # "python" already exists

    def test_edge_case_empty_name(self):
        """Test saving a language with an empty name."""
        language = Language(name="")
        with self.assertRaises(Exception):
            language.save()

    def test_special_characters_in_name(self):
        """Test that special characters in the name are preserved."""
        language = Language.objects.create(name="C#")
        self.assertEqual(language.name, "c#")
        self.assertEqual(str(language), "C#")

    def test_whitespace_in_name(self):
        """Test that leading and trailing whitespace is stripped."""
        language = Language.objects.create(name="   Perl   ")
        self.assertEqual(language.name, "perl")
        self.assertEqual(str(language), "Perl")