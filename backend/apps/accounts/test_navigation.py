from django.test import TestCase
from rest_framework.test import APIClient
from .models import Department, User
from .seed import run as seed_accounts
from .navigation import nav_for


class PersonalNavigationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        seed_accounts()

    def test_unassigned_user_has_only_personal_navigation(self):
        user = User.objects.create_user('unassigned@example.test', 'password')
        keys = [item['key'] for group in nav_for(user) for item in group['items']]
        self.assertEqual(keys, ['dashboard', 'notifications', 'profile'])
        client = APIClient()
        client.force_authenticate(user)
        me = client.get('/api/auth/me/').data
        self.assertEqual(me['home_view'], 'dashboard')
        self.assertEqual(me['visible_departments'], [])

    def test_tech_only_sees_own_department(self):
        user = User.objects.get(email='edwin.ndiritu@prolithica.com')
        client = APIClient()
        client.force_authenticate(user)
        me = client.get('/api/auth/me/').data
        self.assertEqual([d['slug'] for d in me['visible_departments']], ['tech'])
        items = [i for g in me['nav_groups'] for i in g['items']]
        self.assertEqual(items[0]['label'], 'Dashboard')
        self.assertFalse(any(i['count'] for i in items))
        self.assertFalse(any(i['key'] == 'project' for i in items))
        self.assertNotIn('finance', [i['key'] for i in items])

    def test_director_keeps_all_departments(self):
        user = User.objects.filter(role__is_director=True).first()
        client = APIClient()
        client.force_authenticate(user)
        me = client.get('/api/auth/me/').data
        self.assertEqual(len(me['visible_departments']), Department.objects.count())

    def test_unknown_department_does_not_inherit_ceo_navigation(self):
        dept = Department.objects.create(slug='other', label='Other', initials='OT')
        user = User.objects.create_user('other@example.test', 'password', department=dept)
        keys = [i['key'] for g in nav_for(user) for i in g['items']]
        self.assertNotIn('command', keys)
        self.assertNotIn('projects', keys)

    def test_department_api_hides_unrelated_departments(self):
        user = User.objects.get(email='edwin.ndiritu@prolithica.com')
        client = APIClient()
        client.force_authenticate(user)
        self.assertEqual([d['slug'] for d in client.get('/api/departments/').data['results']], ['tech'])

    def test_tech_cannot_bypass_sidebar_with_research_desk_api(self):
        user = User.objects.get(email='edwin.ndiritu@prolithica.com')
        client = APIClient()
        client.force_authenticate(user)
        self.assertEqual(client.get('/api/dashboard/rnd/').status_code, 403)

    def test_executive_keeps_department_access(self):
        user = User.objects.get(email='newton.brian@prolithica.com')
        client = APIClient()
        client.force_authenticate(user)
        self.assertEqual(len(client.get('/api/auth/me/').data['visible_departments']), Department.objects.count())
