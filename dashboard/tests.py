from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from .models import Bot, Server, Command
from django.db.models import Sum

class DashboardViewTests(TestCase):
    def setUp(self):
        # 創建測試用戶
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client = Client()
        
        # 創建測試機器人
        self.bot = Bot.objects.create(
            owner=self.user,
            name='Test Bot',
            token='test-token',
            prefix='!',
            is_active=True
        )
        
        # 創建測試伺服器
        self.server = Server.objects.create(
            bot=self.bot,
            server_id='123456789',
            name='Test Server',
            is_active=True
        )
        
        # 創建測試命令
        self.command = Command.objects.create(
            bot=self.bot,
            name='test',
            uses=10
        )

    def test_index_view(self):
        """測試首頁視圖"""
        # 測試未登入時的回應
        response = self.client.get(reverse('dashboard:index'))
        self.assertEqual(response.status_code, 200)
        
        # 測試登入後的回應
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('dashboard:index'))
        self.assertEqual(response.status_code, 200)
        self.assertTrue('bots_count' in response.context)
        self.assertTrue('servers_count' in response.context)

    def test_home_view(self):
        """測試儀表板主頁視圖"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('dashboard:servers'))
        self.assertEqual(response.status_code, 200)
        self.assertTrue('admin_servers' in response.context)
        self.assertTrue('active_bots' in response.context)
        self.assertTrue('total_commands' in response.context)

    def test_bot_list_view(self):
        """測試機器人列表視圖"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('dashboard:bot:list'))
        self.assertEqual(response.status_code, 200)
        self.assertTrue('bots' in response.context)

    def test_analytics_view(self):
        """測試分析頁面視圖"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('dashboard:analytics:overview'))
        self.assertEqual(response.status_code, 200)
        self.assertTrue('total_bots' in response.context)
        self.assertTrue('active_bots' in response.context)
        self.assertTrue('total_servers' in response.context)
        self.assertTrue('total_commands' in response.context)

    def test_url_patterns(self):
        """測試所有 URL 模式是否正確配置"""
        # 測試主要 URL
        self.assertEqual(reverse('dashboard:index'), '/dashboard/')
        self.assertEqual(reverse('dashboard:servers'), '/dashboard/servers/')
        
        # 測試機器人相關 URL
        self.assertEqual(reverse('dashboard:bot:list'), '/dashboard/bots/')
        self.assertEqual(reverse('dashboard:bot:add'), '/dashboard/bots/add/')
        self.assertEqual(
            reverse('dashboard:bot:detail', kwargs={'bot_id': 1}),
            '/dashboard/bots/1/'
        )
        
        # 測試分析相關 URL
        self.assertEqual(
            reverse('dashboard:analytics:overview'),
            '/dashboard/analytics/'
        )
        
        # 測試認證相關 URL
        self.assertEqual(
            reverse('dashboard:oauth2_login'),
            '/dashboard/oauth2/login/'
        )
        self.assertEqual(
            reverse('dashboard:logout'),
            '/dashboard/logout/'
        ) 