import os.path
import sys

import numpy as np

sys.path.append("..")
import cassiopeia as cass
from cassiopeia import Summoner, Match, MatchHistory
from cassiopeia.data import Season, Queue
from collections import Counter
import arrow
import datetime
import pandas as pd
import time
from tqdm import tqdm
import logging
import json
import itertools
from ..analyzing import champion_classes as cc
from ..analyzing import champion_id_to_name as c_id_to_name
from ..analyzing import champion_class_lookup as cc_lookup
from ..analyzing import ChampionClass
import traceback
import matplotlib.pyplot as plt
import random

REGION = None


class SummonerEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Summoner):
            return obj.name
        return json.JSONEncoder.default(self, obj)


def collect_matches(name: str, region: str, target_match_count: int = 1000):
    global REGION
    REGION = region
    matches = {}
    base_summoner = Summoner(name=name, region=region)
    un_pro_players = initialize_unprocessed(base_summoner)
    pro_players = initialize_processed()
    trigrams = [t for t in itertools.combinations_with_replacement(cc, 3)]
    trigram_index = pd.MultiIndex.from_tuples(trigrams,
                                              names=["class_1", "class_2", "class_3"])
    class_trigrams = initialize_trigrams(trigram_index, trigrams)

    create_report(class_trigrams)
    while True:
        try:
            for summoner in list(un_pro_players.values()):
                time.sleep(1)
                if summoner.id in pro_players:
                    print(
                        f"Summoner {summoner.name} was already processed. I am not smart enough to figure out why such crap may occur. I LITERALLY use dicts AND never insert a player already in pro_players to un_pro_players, i.e only time dif makes sense. But then you notice, that the only players not yet in pro_players are the un_pro_players that will be processed and popped eventually.")
                    continue
                for match in cass.get_match_history(continent=summoner.region.continent, puuid=summoner.puuid,
                                                    queue=Queue.clash):
                    match.participants  # Yikes
                    if len(un_pro_players) < 20:
                        un_pro_players.update({p.summoner.id: p.summoner for p in
                                               (match.blue_team.participants[random.randint(0, 4)],
                                                match.red_team.participants[random.randint(0, 4)])
                                               if p.summoner.id not in pro_players})
                    matches[match.id] = match
                    add_to_trigrams(class_trigrams, match.blue_team)
                    add_to_trigrams(class_trigrams, match.red_team)
                try:
                    un_pro_players.pop(summoner.id)
                    pro_players[summoner.id] = summoner.name
                    if len(matches) > 1000:
                        for key in random.sample(matches.keys(), len(matches) - 1000):
                            del matches[key]
                except:
                    traceback.print_exc()
                    print("no add?")
                    pass

                with open('unprocessed_players.json', 'w') as fp:
                    json.dump(un_pro_players, fp, indent=2, cls=SummonerEncoder)
                with open('processed_players.json', 'w') as fp:
                    json.dump(pro_players, fp, indent=2)
                class_trigrams.to_csv('class_trigrams.csv')
        except cass.datastores.riotapi.common.APIError:
            print("Warning API Error")
            time.sleep(10)
        except Exception as e:
            traceback.print_exc()
            print("Type of Exception", type(e))
            time.sleep(10)


def initialize_unprocessed(base_summoner):
    try:
        with open("unprocessed_players.json") as f:
            summoner_dict = json.load(f)
            return {k: Summoner(id=k, region=REGION) for k, v in summoner_dict.items()}
    except Exception:
        traceback.print_exc()
        return {base_summoner.id: base_summoner}


def initialize_processed():
    try:
        with open("processed_players.json") as f:
            return json.load(f)
    except Exception:
        traceback.print_exc()
        return {}


def initialize_trigrams(trigram_index, trigrams):
    df = pd.DataFrame(np.zeros((len(trigrams), 2)), index=trigram_index, columns=["wins", "games"])
    try:
        base_trigrams = pd.read_csv("class_trigrams.csv")
        base_trigrams.index = df.index
        df["wins"] = base_trigrams["wins"]
        df["games"] = base_trigrams["games"]
    except:
        pass
    return df


def add_to_trigrams(df, team):
    c_classes = [cc_lookup[p.champion.name] for p in team.participants]
    for cs in itertools.combinations(c_classes, 3):
        multi_idx = tuple(sorted(int(c_i) for c_i in cs))
        df.loc[multi_idx]["games"] += 1
        df.loc[multi_idx]["wins"] += team.win


def create_report(tri_grams, n=15):
    print("Champion Class Distribution:")
    for k, v in {c_class: len([c for c in cc_lookup if cc_lookup[c] == c_class]) for c_class in ChampionClass}.items():
        print(f'{k.name}: {v}')
    print("------------------")
    print(f"Plotting Win Rate and Games for the top {n} entries over a total of {sum(tri_grams['games'])} games...")
    cr = range(1, 17)
    one_grams = pd.DataFrame([tri_grams.query(f"class_1 == {i} or class_2 == {i} or class_3 == {i}").sum() for i in cr],
                             index=[i for i in cr])
    one_grams.index.name = "class_1"
    two_index = [
        [i for i in cr for _ in range(i, 17)],
        [j for i in cr for j in range(i, 17)]
    ]
    two_grams = pd.DataFrame([tri_grams.query(make_2d_query(i, j)).sum()
                              for i in cr for j in range(i, 17)], index=two_index)
    two_grams.index.names = ["class_1", "class_2"]

    sort_and_plot(n, one_grams, "Champion Class")
    sort_and_plot(n, two_grams, "Pairs")
    sort_and_plot(n, tri_grams, "Triplets")


def make_2d_query(i, j):
    return " or ".join([f'(class_{ci} == {i} and class_{cj} == {j})' for ci, cj in itertools.permutations([1, 2, 3], 2)])


def sort_and_plot(n, trigrams, group_name):
    by_games = trigrams.sort_values(by=['games'], ascending=False)
    by_games["win_rate"] = by_games["wins"] / by_games["games"]
    by_win_rate = by_games[by_games['games'] > 200].sort_values(by=['win_rate'], ascending=False)
    by_asc_win_rate = by_games[by_games['games'] > 200].sort_values(by=['win_rate'], ascending=True)
    plot_bars(by_games, f"WinRate for most frequent {group_name}", n)
    plot_bars(by_win_rate, f"WinRate for most successful {group_name}", n)
    plot_bars(by_asc_win_rate, f"WinRate for most unsuccessful {group_name}", n)


def plot_bars(df, title, n=16):
    df = df.head(n)
    x = np.arange(len(df))  # the label locations
    width = 0.35  # the width of the bars

    fig, ax = plt.subplots(figsize=(20, 5))
    ax_2nd = ax.twinx()
    ax.bar(x - width / 2, df['games'], width, label='Games')
    rects2 = ax_2nd.bar(x + width / 2, df['win_rate'], width, label='Win Rate', color='orange')

    # Add some text for labels, title and custom x-axis tick labels, etc.
    ax.set_ylabel('Games Played')
    ax_2nd.set_ylabel('Win Rate')
    ax.set_title(title)
    ax.set_xticks(x, translate_classes(df), fontsize='small')

    ax_2nd.bar_label(rects2, padding=3, fmt='%.2f')
    ax_2nd.set_ylim(0, 1.05)
    ax.legend()
    ax_2nd.legend()

    fig.tight_layout()

    plt.show()


def translate_classes(trigrams):
    trigrams = trigrams.reset_index()
    string_enums = [trigrams[f'class_{i + 1}'].apply(lambda x: str(ChampionClass(x))[14:]).tolist() for i in
                    range(trigrams.shape[1] - 3)]
    return ["\n".join(classes) for classes in zip(*string_enums)]


sadfas = """
def compute_champion_win_rates(matches):
    games = Counter()
    wins = Counter()
    for m in matches.values():
        for p in m.participants:
            games[p.champion.id] += 1
            wins[p.champion.id] += (p in m.blue_team.participants) ^ m.red_team.win
    df = pd.DataFrame.from_records([(c_id, c_id_to_name[c_id], games[c_id], wins[c_id]) for c_id in games],
                                   columns=["champion_id", "champion_name", "games", "wins"])
    df["win_rate"] = df["wins"] / df["games"]
    return df
"""
