from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist
from .models import CustomUser, MedjilTOTPDevice
#permissions to admin_group
@receiver(post_save, sender=CustomUser)
def set_admin_permissions(sender, instance, **kwargs):
    admin_group = Group.objects.filter(name='Admin').first()
    permissions = Permission.objects.all()
    admin_group.permissions.add(*permissions)

    # ==> Add users to groups
    admin_users = ['kent.wheeler@landgate.wa.gov.au', 
                    'khandu.k@landgate.wa.gov.au',
                    'irek.baran@landgate.wa.gov.au',
                    'brendon.hellmund@landgate.wa.gov.au',
                    'vanessa.ung@landgate.wa.gov.au',
                    'michael.kuhn@landgate.wa.gov.au']
    for email in admin_users:
        try:
            user_id = CustomUser.objects.get(email = email)
            admin_group.user_set.add(user_id)
        except ObjectDoesNotExist:
            pass

# permissions to verifying_authority_group - permission for TOTPDevice excluded
@receiver(post_save, sender=CustomUser)
def set_verifying_authority_permissions(sender, instance, **kwargs):
    verifying_authority_group = Group.objects.filter(name='Verifying_Authority').first()
    permissions = Permission.objects.exclude(codename__startswith='delete_')
    # ==> Add users to groups
    landgate_users = ['kent.wheeler@landgate.wa.gov.au',
                    'tony.castelli@landgate.wa.gov.au',
                    'david.martin@landgate.wa.gov.au',
                    'martin.cole@landgate.wa.gov.au',
                    'brendon.hellmund@landgate.wa.gov.au',
                    'khandu.k@landgate.wa.gov.au',]
    
    for email in landgate_users:
        try:
            user_id = CustomUser.objects.get(email = email)
            verifying_authority_group.user_set.add(user_id)
        except ObjectDoesNotExist:
            pass

    content_type_to_exclude = ContentType.objects.get_for_model(MedjilTOTPDevice)
    # Add all permissions except for the excluded model
    for permit in permissions:
        if permit.content_type != content_type_to_exclude or permit.codename.startswith('view'):
            verifying_authority_group.permissions.add(permit)