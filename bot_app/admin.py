from django.contrib import admin
from .models import Game, Profile


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ['username', 'steam', 'game', 'active']


admin.site.register(Game)
