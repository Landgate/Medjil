from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist
from .models import CustomUser, MedjilTOTPDevice
#permissions to admin_group
admin_group = Group.objects.filter(name='Admin').first()
permissions = Permission.objects.all()
admin_group.permissions.add(*permissions)

# ==> Add users to groups
admin_users = ['kent.wheeler@landgate.wa.gov.au', 
               'khandu.k@landgate.wa.gov.au']
for email in admin_users:
    try:
        user_id = CustomUser.objects.get(email = email)
        admin_group.user_set.add(user_id)
    except ObjectDoesNotExist:
        pass

# permissions to geodesy_group
geodesy_group = Group.objects.filter(name='Geodesy').first()
permissions = Permission.objects.exclude(codename__startswith='delete_')
# geodesy_group.permissions.add(*permissions)
# ==> Add users to groups
geodesy_users = ['irek.baran@landgate.wa.gov.au',
                'tony.castelli@landgate.wa.gov.au',
                'brendon.hellmund@landgate.wa.gov.au',
                'vanessa.ung@landgate.wa.gov.au',
                'khandu.k@landgate.wa.gov.au',
                'michael.kuhn@landgate.wa.gov.au']
for email in geodesy_users:
    try:
        user_id = CustomUser.objects.get(email = email)
        geodesy_group.user_set.add(user_id)
    except ObjectDoesNotExist:
        pass

content_type_to_exclude = ContentType.objects.get_for_model(MedjilTOTPDevice)
# Add all permissions except for the excluded model
for permit in permissions:
    if permit.content_type != content_type_to_exclude or permit.codename.startswith('view'):
        geodesy_group.permissions.add(permit)


# # Get the content type for the MedjilTOTPDevice
# content_type = ContentType.objects.get_for_model(MedjilTOTPDevice)
# # allow only view permission for TOTP devices for geodesy_group
# view_permission = Permission.objects.get(codename='view_medjiltotpdevice', content_type = content_type)
# # Set permission
# geodesy_group.permissions.set([view_permission])