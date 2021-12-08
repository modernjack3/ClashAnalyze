from src.analyzing.test import collect_matches
from src.analyzing.test import compute_champion_win_rates
import logging
import cassiopeia as cass
import os

if __name__ == '__main__':
    logging.basicConfig(level=logging.WARNING, force=True)
    cass.apply_settings(os.path.join("..", "..", "..", "..", "..", "ClashAnalyze", "cassiopeia.json"))
    matches = collect_matches(name="µDerAnonym", region="EUW", target_match_count=30)
    champion_win_rates = compute_champion_win_rates(matches)
    logging.warning(champion_win_rates)

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
