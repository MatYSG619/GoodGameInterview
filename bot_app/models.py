from django.db import models


class Game(models.Model):
    name = models.CharField(max_length=150, unique=True, verbose_name='Название игры')

    class Meta:
        verbose_name = 'Игра'
        verbose_name_plural = 'Игры'

    def __str__(self):
        return self.name


class Profile(models.Model):
    username = models.TextField(blank=True, verbose_name='Имя пользователя')
    chat_id = models.TextField(blank=True, verbose_name='Номер чата')
    steam = models.TextField(blank=True, verbose_name='Логин стим')
    about = models.TextField(blank=True, verbose_name='О себе')
    game = models.TextField(blank=True, verbose_name='Игра')
    active = models.BooleanField(default=True, verbose_name='Поиск')
    step = models.PositiveIntegerField(default=0, verbose_name='Счетчик')
    choice = models.TextField(blank=True, verbose_name="Выбранный пользователь")

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return self.username
