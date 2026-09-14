from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient
from apps.accounts.models import User, Department, Role
from apps.delivery.models import Project, ProjectMember, Task
from .models import DailyLog, Thread, Message

class WorkspaceTests(TestCase):
    def setUp(self):
        self.client=APIClient()
        self.department=Department.objects.create(slug='engineering',label='Engineering')
        self.other_department=Department.objects.create(slug='finance',label='Finance')
        self.director=Role.objects.create(slug='director',label='CEO',is_director=True)
        self.employee_role=Role.objects.create(slug='employee',label='Employee',scope='assigned_projects')
        self.ceo=User.objects.create_user('ceo@example.com','Company-pass-123',display_name='CEO',role=self.director)
        self.hod=User.objects.create_user('hod@example.com','Company-pass-123',display_name='Head',department=self.department,is_department_head=True,role=self.employee_role)
        self.employee=User.objects.create_user('one@example.com','Company-pass-123',display_name='One',department=self.department,role=self.employee_role)
        self.other=User.objects.create_user('other@example.com','Company-pass-123',display_name='Other',department=self.other_department,role=self.employee_role)
        self.project=Project.objects.create(name='Test Project')
        ProjectMember.objects.create(project=self.project,user=self.hod)
    def login_as(self,user): self.client.force_authenticate(user)
    def test_real_account_number_password_and_suspension(self):
        self.login_as(self.ceo)
        payload={'display_name':'New employee','email':'new@example.com','password':'Fresh-company-pass-293','department':str(self.department.pk),'role':str(self.employee_role.pk)}
        response=self.client.post('/api/users/',payload); self.assertEqual(response.status_code,201,response.data)
        user=User.objects.get(email='new@example.com'); self.assertEqual(user.employee_number,'EN-P005');self.assertTrue(user.check_password(payload['password']))
        self.assertNotIn('password',response.data)
        self.client.force_authenticate(None)
        response=self.client.post('/api/auth/login/',{'email':user.email,'password':payload['password']});self.assertEqual(response.status_code,200)
        token=response.data['access']
        self.login_as(self.ceo);self.client.patch(f'/api/users/{user.pk}/',{'state':'suspended'})
        self.client.force_authenticate(None);self.client.credentials(HTTP_AUTHORIZATION='Bearer '+token)
        self.assertEqual(self.client.get('/api/workspace/').status_code,401)
        self.client.credentials();self.assertEqual(self.client.post('/api/auth/login/',{'email':user.email,'password':payload['password']}).status_code,403)
    def test_employee_cannot_manage_users(self):
        self.login_as(self.employee);self.assertEqual(self.client.get('/api/users/').status_code,403)
    def test_hod_department_assignment_and_profile(self):
        self.login_as(self.hod)
        payload={'text':'Build a form','project':str(self.project.pk),'assignee':str(self.employee.pk)}
        response=self.client.post('/api/workspace/',payload);self.assertEqual(response.status_code,201,response.data)
        payload['assignee']=str(self.other.pk);self.assertEqual(self.client.post('/api/workspace/',payload).status_code,404)
        self.login_as(self.employee)
        self.assertEqual(len(self.client.get('/api/profile/').data['projects']),1)
        self.assertEqual(self.client.post('/api/workspace/',payload).status_code,403)
    def test_daily_logs_owned_and_scoped(self):
        ProjectMember.objects.create(project=self.project,user=self.employee)
        self.login_as(self.employee)
        payload={'project':str(self.project.pk),'date':str(timezone.localdate()),'minutes':90,'summary':'Implemented form','user':str(self.other.pk)}
        self.assertEqual(self.client.post('/api/workspace/logs/',payload).status_code,201)
        self.assertEqual(DailyLog.objects.get().user,self.employee)
        payload['minutes']=1500;self.assertEqual(self.client.post('/api/workspace/logs/',payload).status_code,400)
        self.login_as(self.other);self.assertEqual(self.client.get('/api/workspace/').data['logs'],[])
        self.assertEqual(self.client.post('/api/workspace/logs/',payload).status_code,400)
    def test_group_admin_and_private_direct_messages(self):
        self.login_as(self.employee)
        response=self.client.post('/api/workspace/threads/',{'name':'Engineering','members':[str(self.hod.pk)],'direct':False},format='json')
        self.assertEqual(response.status_code,201,response.data);group=Thread.objects.get(pk=response.data['id']);self.assertIn(self.ceo,group.members.all())
        response=self.client.post('/api/workspace/threads/',{'members':[str(self.hod.pk)],'direct':True},format='json')
        direct=response.data['id'];self.client.post(f'/api/workspace/threads/{direct}/messages/',{'body':'Private note'})
        self.assertEqual(Message.objects.get().body,'Private note')
        self.login_as(self.ceo);self.assertEqual(self.client.get(f'/api/workspace/threads/{direct}/messages/').status_code,404)
        self.assertEqual(self.client.get(f'/api/workspace/threads/{group.pk}/messages/').status_code,200)
        self.login_as(self.other);self.assertEqual(self.client.get(f'/api/workspace/threads/{group.pk}/messages/').status_code,404)
        self.login_as(self.hod)
        again=self.client.post('/api/workspace/threads/',{'members':[str(self.employee.pk)],'direct':True},format='json')
        self.assertEqual(str(again.data['id']),str(direct))
    def test_task_completion_cannot_cross_departments(self):
        task=Task.objects.create(project=self.project,assignee=self.employee,text='Scoped task')
        self.login_as(self.other)
        self.assertEqual(self.client.patch(f'/api/workspace/tasks/{task.pk}/',{'done':True},format='json').status_code,404)
        self.login_as(self.employee)
        self.assertEqual(self.client.patch(f'/api/workspace/tasks/{task.pk}/',{'done':True},format='json').status_code,200)
    def test_ceo_cannot_remove_own_access(self):
        self.login_as(self.ceo)
        self.assertEqual(self.client.patch(f'/api/users/{self.ceo.pk}/',{'state':'suspended'}).status_code,400)
        self.assertEqual(self.client.post(f'/api/users/{self.ceo.pk}/grant/',{'role':'employee'}).status_code,400)

    def test_only_ceo_can_manage_group_members(self):
        self.login_as(self.employee)
        response=self.client.post('/api/workspace/threads/',{'name':'Team','members':[str(self.hod.pk)]},format='json')
        path=f"/api/workspace/threads/{response.data['id']}/messages/"
        self.assertEqual(self.client.patch(path,{'members':[str(self.other.pk)]},format='json').status_code,403)
        self.login_as(self.ceo)
        self.assertEqual(self.client.patch(path,{'name':'Updated team','members':[str(self.other.pk)]},format='json').status_code,200)
        self.login_as(self.employee);self.assertEqual(self.client.get(path).status_code,404)
        self.login_as(self.other);self.assertEqual(self.client.get(path).status_code,200)

    def test_client_portal_accounts_cannot_open_employee_workspace_or_chat(self):
        portal_role=Role.objects.create(slug='client_portal',label='Client portal',scope='own_records')
        portal=User.objects.create_user('portal@example.com','Company-pass-123',display_name='Portal User',role=portal_role)
        self.login_as(portal)
        self.assertEqual(self.client.get('/api/workspace/').status_code,403)
        self.assertEqual(self.client.get('/api/workspace/threads/').status_code,403)
        self.assertEqual(self.client.post('/api/workspace/threads/',{'name':'Attempt','members':[str(self.employee.pk)]},format='json').status_code,403)

    def test_project_setup_is_repeatable_and_keeps_company_edits(self):
        from django.core.management import call_command
        historical=Project.objects.create(ref='PRJ-041',name='LIMS',full_name='LIMS')
        call_command('setup_workspace',verbosity=0)
        historical.refresh_from_db()
        self.assertEqual(historical.name,'LIMS (legislative information system)')
        self.assertEqual(Project.objects.filter(name__in=[
            'Bunema billing system','PBO Workflow','Expresscarpets','Kienyeji Hub',
            'Goalhub','Partec internal system','LIMS (legislative information system)',
            'Directorate of Committees system']).count(),8)
        self.assertEqual(Project.objects.get(name='Bunema billing system').ref,'PRJ-046')
        self.assertEqual(Project.objects.get(name='Expresscarpets').ref,'PRJ-042')
        historical.name='Approved project title'
        historical.stage='Delivery'
        historical.save()
        call_command('setup_workspace',verbosity=0)
        historical.refresh_from_db()
        self.assertEqual((historical.name,historical.stage),('Approved project title','Delivery'))

    def test_bunema_has_its_own_stable_ref_and_legacy_portal_is_archived(self):
        from django.core.management import call_command
        history=Project.objects.create(ref="PRJ-030",name="AN-PBO Data Portal",contract_value=12345,is_archived=True)
        old_task=Task.objects.create(project=history,assignee=self.employee,text="Existing portal task")
        call_command("setup_workspace",verbosity=0)
        history.refresh_from_db()
        bunema=Project.objects.get(ref="PRJ-046")
        self.assertEqual((bunema.name,bunema.contract_value),("Bunema billing system",0))
        self.assertTrue(history.is_archived)
        self.assertEqual((history.name,history.contract_value),("AN-PBO Data Portal",12345))
        self.assertEqual(Task.objects.get(pk=old_task.pk).project_id,history.pk)
        self.login_as(self.ceo)
        response=self.client.get("/api/workspace/")
        self.assertNotIn("AN-PBO Data Portal",[row["name"] for row in response.data["projects"]])
        self.assertEqual(self.client.get(f"/api/projects/{history.pk}/").status_code,404)
        self.assertEqual(self.client.get(f"/api/projects/{bunema.pk}/").status_code,200)

    def test_fresh_install_bootstraps_one_secure_ceo_interactively(self):
        from django.core.management import call_command
        from io import StringIO
        from unittest.mock import patch
        from apps.workforce.management.commands import bootstrap_ceo
        self.ceo.delete()
        output=StringIO()
        with patch('sys.stdin.isatty',return_value=True), patch('builtins.input',return_value='first-ceo@example.com'), patch.object(bootstrap_ceo,'getpass',side_effect=['Secure-first-company-pass-738','Secure-first-company-pass-738']):
            call_command('bootstrap_ceo',stdout=output)
        owner=User.objects.get(email='first-ceo@example.com')
        self.assertTrue(owner.is_superuser)
        self.assertTrue(owner.role.is_director)
        self.assertTrue(owner.check_password('Secure-first-company-pass-738'))
        self.assertRegex(owner.employee_number,r'^EN-P\d{3,}$')
        with patch('builtins.input',side_effect=AssertionError('must not prompt again')):
            call_command('bootstrap_ceo',stdout=output)
        self.assertEqual(User.objects.filter(role__is_director=True).count(),1)
