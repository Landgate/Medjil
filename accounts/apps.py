'''

   © 2023 Western Australian Land Information Authority

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.

'''
from django.apps import AppConfig
from django.db.models.signals import post_migrate
from django.dispatch import receiver

class AppAccountsConfig(AppConfig):
    name = 'accounts'

    def ready(self):
        import accounts.signals  # noqa

        @receiver(post_migrate)
        def connect_signals(sender, **kwargs):
            from django.db.models.signals import post_save
            from .models import CustomUser
            
            from accounts.signals import set_admin_permissions
            from accounts.signals import set_verifying_authority_permissions

            post_save.connect(set_admin_permissions, sender=CustomUser)
            post_save.connect(set_verifying_authority_permissions, sender=CustomUser)