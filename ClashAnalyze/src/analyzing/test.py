import cassiopeia as cass
from cassiopeia import Summoner, Match, MatchHistory
from cassiopeia.data import Season, Queue
from collections import Counter
import arrow
import datetime
import pandas as pd
import time
from tqdm import tqdm

c_id_to_name = {champion.id: champion.name for champion in cass.get_champions(region="EUW")}


def collect_matches(name: str, region: str, target_match_count: int = 1000):
    matches = {}
    base_summoner = Summoner(name=name, region=region)
    un_pro_players = {base_summoner.id: base_summoner}
    pro_players = {}
    progress_bar = tqdm(total=target_match_count)
    while True:
        for summoner in list(un_pro_players.values()):
            time.sleep(1)
            for match in cass.get_match_history(continent=summoner.region.continent, puuid=summoner.puuid,
                                                queue=Queue.clash):
                match.participants  # Yikes
                un_pro_players.update({p.summoner.id: p.summoner for p in
                                       (match.blue_team.participants[0], match.red_team.participants[0])
                                       if p not in pro_players})
                try:
                    un_pro_players.pop(summoner.id)
                    pro_players[summoner.id] = summoner
                except:
                    pass
                matches[match.id] = match
                progress_bar.update(len(matches) - progress_bar.n)
                if len(matches) >= target_match_count:
                    return matches


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


if __name__ == "__main__":
    cass.set_riot_api_key("---")
    matches = collect_matches(name="µDerAnonym", region="EUW", target_match_count=50)
    champion_win_rates = compute_champion_win_rates(matches)
    print(champion_win_rates)
