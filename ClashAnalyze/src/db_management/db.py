import psycopg2
import logging
from datetime import datetime


class db_connector:

    def __init__(self):

        # Read the config to connect to the database
        with open("creds.cfg", "r") as f:
            lines = f.readlines()
            address, db_name, user, password = [x.split(":")[1][:-1] for x in lines]

        # Establish a connection to the database
        try:
            self.con = psycopg2.connect(
                host=address,
                database=db_name,
                user=user,
                password=password)
        except Exception as ex:
            logging.critical(ex)
            exit()

        logging.info("Database Connection successful")

    # Insert a player to the player table -> datetime is optional - default is current time
    def insert_player(self, puuid: str, ign: str, rank: int, region: str,
                      date: str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")):
        cur = self.con.cursor()

        statement = "INSERT INTO players(puuid, ign, rank, region, last_update) VALUES('{0}','{1}','{2}','{3}','{4}')" \
                    "ON CONFLICT (puuid) DO UPDATE SET ign='{1}', rank='{2}', region='{3}', last_update='{4}'"\
                    .format(puuid, ign, str(rank), region, date)

        cur.execute(statement)
        self.con.commit()
        cur.close()

    # Get a player by puuid
    def get_player_puuid(self, puuid: str):
        return None

    # Get a player by IGN and Region (Default Region is EUW)
    def get_player_ign(self, ign: str, region: str = "EUW"):
        return None

    # Get all players of a rank
    def get_players_rank(self, rank: int):
        return None