from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.views import View
from django.template import loader
from plotly.offline import plot as plotly
from plotly.graph_objs import Scatter

from django_cassiopeia import cassiopeia as cass
from collections import Counter


def index(request):
    latest_question_list = list(range(6))
    template = loader.get_template('polls/plot.html')
    context = {
        'latest_question_list': latest_question_list,
    }
    return HttpResponse(template.render(context, request))


class PlayerCounter:

    def __init__(self, summoner):
        self.summoner = summoner
        self.id = summoner.puuid
        self.name = summoner.name
        self.c = 0

    def incr(self):
        self.c += 1


def plot(request, player_name):
    summoner = cass.Summoner(name=player_name, region="EUW")
    matches = cass.get_match_history(continent=summoner.region.continent, puuid=summoner.puuid)

    occ = {}
    for match in matches:
        for p in match.participants:
            if p.summoner.id not in occ:
                occ[p.summoner.id] = PlayerCounter(p.summoner)
            occ[p.summoner.id].incr()

    x_data = [0, 1, 2, 3]
    y_data = [x ** 2 for x in x_data]
    plot_div = plotly([Scatter(x=x_data, y=y_data,
                               mode='lines', name='test',
                               opacity=0.8, marker_color='green')],
                      output_type='div')
    return render(request, "polls/plot.html",
                  context={'plot_div': plot_div, 'puuid': summoner.puuid, 'occurrences': list(occ.values())})
