from django.db import models

from django.db import models


class Question(models.Model):
    question_text = models.CharField(max_length=200)
    pub_date = models.DateTimeField('date published')


class Choice(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    choice_text = models.CharField(max_length=200)
    votes = models.IntegerField(default=0)


class Player(models.Model):
    player_name = models.CharField('Player Name', max_length=20)
    matches = []

    def __str__(self):
        player_name = self.player_name
        matches = self.matches
        return f'{{{player_name=}, {matches=}}}'

    def __repr__(self):
        return self.__str__()

    def populate(self):
        self.matches += [len(self.matches)]
