from django.test import TestCase
from .models import Syllabus

class SyllabusModelTest(TestCase):
    def setUp(self):
        Syllabus.objects.create(title="Math 101", description="Introduction to Mathematics")
    
    def test_syllabus_creation(self):
        syllabus = Syllabus.objects.get(title="Math 101")
        self.assertEqual(syllabus.description, "Introduction to Mathematics")

class SyllabusViewTest(TestCase):
    def test_syllabus_view_status_code(self):
        response = self.client.get('/syllabus/')
        self.assertEqual(response.status_code, 200)

    def test_syllabus_view_template(self):
        response = self.client.get('/syllabus/')
        self.assertTemplateUsed(response, 'syllabus/syllabus_display.html')