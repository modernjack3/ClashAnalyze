from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.views import View
from django.template import loader
from plotly.offline import plot as plotly
from plotly.graph_objs.scatter.marker import Line
from plotly.subplots import make_subplots
import plotly.express as px
import arrow
import pandas as pd

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


def m_start(m):
    return m.start


def plot(request, player_name):
    summoner = cass.Summoner(name=player_name, region="EUW")
    # matches = cass.get_match_history(continent=summoner.region.continent, puuid=summoner.puuid)
    # start = min((m for m in matches), key=m_start).start.shift(minutes=-10)
    # occ = {}
    # for match in matches:
    #     for p in match.participants:
    #         if p.summoner.id not in occ:
    #             occ[p.summoner.id] = PlayerCounter(p.summoner)
    #         occ[p.summoner.id].incr()
    # occ = {k: v for k, v in occ.items() if v.c > 2}
    # for player in occ.values():
    #     player.matches = sorted(cass.get_match_history(continent=player.summoner.region.continent,
    #                                                    puuid=player.summoner.puuid, begin_time=start), key=m_start)
    # df = pd.DataFrame(data={
    #     'time': [m.start.timestamp for player in occ.values() for m in player.matches],
    #     'player_idx': [i for i, player in enumerate(occ.values()) for _ in player.matches],
    #     'player': [player.name for player in occ.values() for _ in player.matches]})
    # df.to_csv("maria.csv")
    df = pd.read_csv("maria.csv")
    df = df[df["time"] >= 1639315814]  # TODO: This is currently Marys first game

    df['datetime'] = [arrow.get(t) for t in df['time']]
    time = sorted(df['time'])
    large_gaps = [(arrow.get(t1).shift(hours=1), arrow.get(t2).shift(hours=-1)) for t1, t2 in zip(time[:-1], time[1:])
                  if t2 - t1 > 8 * 60 * 60]
    cut_points = [arrow.get(time[0]).shift(minutes=-5)] + [t for gap in large_gaps for t in gap] + [
        arrow.get(time[-1]).shift(minutes=+5)]

    pre = pd.DataFrame(data={
        'time': [cut_points[0].shift(minutes=-6, seconds=-i).timestamp for i, player in
                 enumerate(df['player'].unique())],
        'datetime': [cut_points[0].shift(minutes=-6, seconds=-i) for i, player in enumerate(df['player'].unique())],
        'player_idx': [i for i, player in enumerate(df['player'].unique())],
        'player': [player for player in df['player'].unique()]})
    post = pd.DataFrame(data={
        'time': [cut_points[-1].shift(minutes=+6, seconds=+i).timestamp for i, player in
                 enumerate(df['player'].unique())],
        'datetime': [cut_points[-1].shift(minutes=+6, seconds=+i) for i, player in enumerate(df['player'].unique())],
        'player_idx': [i for i, player in enumerate(df['player'].unique())],
        'player': [player for player in df['player'].unique()]})
    df = pre.append(df)
    df = df.append(post)
    cols = len(large_gaps) + 1
    cuts_sum = sum(
        [(right.timestamp - left.timestamp) + 600 for left, right in zip(cut_points[0::2], cut_points[1::2])])
    fig = make_subplots(
        rows=1, cols=cols,
        horizontal_spacing=0.02,
        shared_yaxes=True, column_widths=[(right.timestamp - left.timestamp) + 600 / cuts_sum
                                          for left, right in zip(cut_points[0::2], cut_points[1::2])]
    )

    df['player_idx_merge'] = [min(df[df['time'] == t]['player_idx']) + 0.1 * p_idx
                              for t, p_idx in zip(df['time'], df['player_idx'])]

    lines = px.line(df, x="datetime", y="player_idx_merge", color='player', markers=True)

    fig.add_traces(lines.data, rows=1, cols=1)
    for trace in lines.data:
        trace.showlegend = False
    for i in range(1, cols):
        fig.add_traces(lines.data, rows=1, cols=i + 1)
    for i, (left, right) in enumerate(zip(cut_points[0::2], cut_points[1::2])):
        fig.update_yaxes(visible=False, row=1, col=i + 1)
        fig.update_xaxes(range=[left, right], row=1, col=i + 1, tickangle=45, dtick=4 * 60 * 60 * 1000.0)

    plot_div = plotly(fig, output_type='div')
    return render(request, "polls/plot.html",
                  context={'plot_div': plot_div, 'puuid': summoner.puuid, 'occurrences': list()})
