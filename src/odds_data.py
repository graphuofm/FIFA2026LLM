"""Market odds per match, collected by fetching the pre-match preview/odds
articles the models themselves cited (source URL recorded per row).

Raw odds are stored as pulled from each article. Format is auto-detected:
  * American moneyline: "+155", "-250"
  * fractional:         "11/1", "2/9", "7/10"
Both are normalised to decimal odds and implied probability by build_odds.py.

odds[match_id] = (home, draw, away, book, source_url)
"""

ODDS = {
    "m01": ("-250", "+360", "+700", "FanDuel", "https://www.cbssports.com/soccer/news/mexico-south-africa-odds-prediction-time-2026-world-cup-picks-line-soccer-best-bets/"),
    "m02": ("+155", "+215", "+185", "Kalshi", "https://www.covers.com/world-cup/south-korea-vs-czechia-picks-predictions-odds-today-june-11-2026"),
    # m03 pending (lineups.com 403) — retry with fallback
    "m04": ("-120", "+265", "+370", "unspecified", "https://www.cbssports.com/soccer/news/canada-bosnia-world-cup-2026-preview-predictions-watch-odds/"),
    "m05": ("11/1", "11/2", "2/9", "bet365", "https://www.racingpost.com/sport/football-tips/world-cup-2026/qatar-vs-switzerland-betting-tips-predictions-team-news-odds-bet-builder-a3Es28q4twWR/"),
    "m06": ("-167", "+290", "+400", "unspecified", "https://www.cbssports.com/soccer/news/brazil-morocco-world-cup-2026-preview-predictions-watch/"),
    "m07": ("+525", "+375", "-170", "Kalshi", "https://www.covers.com/world-cup/haiti-vs-scotland-prediction-picks-odds-saturday-6-13-2026"),
    "m08": ("4/1", "11/4", "7/10", "bet365", "https://www.racingpost.com/sport/football-tips/world-cup-2026/australia-vs-turkey-world-cup-prediction-team-news-odds-betting-tips-and-bet-builder-aDqeC7S5q8Ib/"),
    "m09": ("1/25", "18/1", "33/1", "Paddy Power", "https://www.racingpost.com/sport/football-tips/world-cup-2026/germany-vs-curacao-world-cup-prediction-team-news-odds-betting-tips-and-bet-builder-aCceV7d7CMtv/"),
    "m03": ("-105", "+240", "+320", "FanDuel", "https://www.foxsports.com/stories/soccer/2026-world-cup-usa-paraguay-odds-prediction-picks"),
    "m10": ("1/1", "5/2", "13/5", "Ladbrokes", "https://www.racingpost.com/sport/football-tips/world-cup-2026/netherlands-vs-japan-world-cup-prediction-team-news-odds-betting-tips-and-bet-builder-aHebD0x5a8Gy/"),
    "m11": ("5/2", "7/4", "7/5", "Paddy Power", "https://www.racingpost.com/sport/football-tips/world-cup-2026/ivory-coast-vs-ecuador-world-cup-prediction-team-news-odds-betting-tips-and-bet-builder-aOFLB3P6BDFL/"),
    "m12": ("9/10", "12/5", "10/3", "bet365", "https://www.racingpost.com/sport/football-tips/world-cup-2026/sweden-vs-tunisia-world-cup-prediction-team-news-odds-betting-tips-and-bet-builder-a1p2W8G103pO/"),
    "m13": ("-1011", "+1329", "+2400", "Kalshi", "https://www.covers.com/world-cup/spain-vs-cape-verde-prediction-picks-odds-monday-6-15-2026"),
    "m14": ("5/6", "12/5", "15/4", "bet365", "https://www.racingpost.com/sport/football-tips/world-cup-2026/iran-vs-new-zealand-world-cup-prediction-team-news-odds-betting-tips-and-bet-builder-aAP7j4z779qD/"),
    "m15": ("+733", "+280", "-212", "Kalshi", "https://www.covers.com/world-cup/saudi-arabia-vs-uruguay-prediction-picks-odds-monday-6-15-2026"),
    "m16": ("-155", "+285", "+425", "unspecified", "https://www.cbssports.com/soccer/news/belgium-vs-egypt-world-cup-2026-preview-predictions-watch/"),
    "m18": ("-220", "+350", "+600", "FanDuel", "https://www.cbssports.com/soccer/news/france-senegal-odds-prediction-time-2026-world-cup-picks-best-bets/"),
    "m19": ("12/1", "6/1", "1/5", "bet365", "https://www.racingpost.com/sport/football-tips/world-cup-2026/iraq-vs-norway-world-cup-prediction-team-news-odds-betting-tips-and-bet-builder-aaXwW1a7805C/"),
    "m20": ("-245", "+376", "+809", "Kalshi", "https://www.covers.com/world-cup/argentina-vs-algeria-prediction-picks-odds-tuesday-6-16-2026"),
    "m21": ("-370", "+460", "+1100", "FanDuel", "https://www.cbssports.com/soccer/news/portugal-dr-congo-odds-prediction-time-2026-world-cup-picks-best-bets/"),
    "m22": ("-143", "+265", "+430", "BetMGM", "https://www.sportsgambler.com/betting-tips/football/england-vs-croatia-prediction-lineups-odds-2026-06-17/"),
    "m24": ("15/2", "7/2", "2/5", "bet365", "https://www.racingpost.com/sport/football-tips/world-cup-2026/uzbekistan-vs-colombia-world-cup-prediction-team-news-odds-betting-tips-and-bet-builder-arLVQ9O2OR9D/"),
    "m17": ("-260", "+370", "+700", "FanDuel", "https://www.cbssports.com/soccer/news/austria-jordan-odds-prediction-time-2026-world-cup-picks-soccer-best-bets/"),
    "m25": ("+104", "+245", "+317", "Kalshi", "https://www.covers.com/world-cup/mexico-vs-south-korea-prediction-picks-odds-thursday-6-18-2026"),
    "m26": ("-385", "+475", "+875", "Kalshi", "https://www.covers.com/world-cup/canada-vs-qatar-prediction-picks-odds-thursday-6-18-2026"),
    "m27": ("1.57", "4.00", "5.80", "Dafabet", "https://www.toffeeweb.com/int/switzerland-vs-bosnia-and-herzegovina-predictions-picks-odds-19-06-2026/"),
    "m28": ("-125", "+270", "+350", "FanDuel", "https://www.foxsports.com/stories/soccer/2026-world-cup-czechia-south-africa-odds-prediction-picks"),
    "m29": ("-160", "+320", "+420", "FanDuel", "https://www.cbssports.com/soccer/news/usmnt-australia-odds-prediction-time-2026-world-cup-picks-soccer-bets/"),
    "m30": ("+105", "+230", "+280", "FanDuel", "https://www.foxsports.com/stories/soccer/2026-world-cup-turkiye-paraguay-odds-prediction-picks"),  # vsin article had wrong (m03) odds; corrected via FanDuel
    "m32": ("4/1", "13/5", "8/11", "bet365", "https://www.racingpost.com/sport/football-tips/world-cup-2026/scotland-vs-morocco-world-cup-prediction-team-news-odds-betting-tips-and-bet-builder-aTSK61a9KSIm/"),
    "m33": ("11/2", "3/1", "8/15", "bet365", "https://www.racingpost.com/sport/football-tips/world-cup-2026/tunisia-vs-japan-predictions-team-news-odds-betting-tips-bet-builder-a1nmS7s9uYmG/"),
    "m34": ("-1000", "+900", "+2000", "Kalshi", "https://www.covers.com/world-cup/uruguay--vs-cape-verde-prediction-picks-odds-sunday-6-21-2026"),  # covers page served Ecuador-Curacao content
    "m35": ("-182", "+370", "+450", "Kalshi", "https://www.covers.com/world-cup/germany-vs-ivory-coast-prediction-picks-odds-saturday-6-20-2026"),
    "m36": ("8/11", "14/5", "15/4", "Ladbrokes", "https://www.racingpost.com/sport/football-tips/world-cup-2026/netherlands-vs-sweden-betting-tips-predictions-team-news-odds-bet-builder-awlZS3M1PcnW/"),
    "m37": ("9/2", "3/1", "6/10", "bet365", "https://www.racingpost.com/sport/football-tips/world-cup-2026/new-zealand-vs-egypt-betting-tips-predictions-team-news-odds-bet-builder-abyHq6P5efqn/"),
    "m31": ("-800", "+850", "+1900", "BetOnline", "https://thesportsrush.com/brazil-v-haiti-predictions/"),
    "m39": ("-230", "+360", "+650", "unspecified", "https://www.cbssports.com/soccer/news/belgium-vs-iran-world-cup-2026-preview-predictions-watch/"),
    "m40": ("-1100", "+1100", "+2000", "FanDuel", "https://www.cbssports.com/soccer/news/spain-saudi-arabia-odds-prediction-time-2026-world-cup-picks-best-bets/"),
    "m41": ("9/2", "31/10", "4/7", "bet365", "https://www.racingpost.com/sport/football-tips/world-cup-2026/jordan-vs-algeria-betting-tips-predictions-team-news-odds-bet-builder-abUG75Z79uPM/"),
    "m42": ("+127", "+270", "+222", "Kalshi", "https://www.covers.com/world-cup/norway-vs-senegal-prediction-picks-odds-monday-6-22-2026"),
    "m43": ("-1200", "+1000", "+2500", "Kalshi", "https://www.covers.com/world-cup/france-vs-iraq-prediction-picks-odds-monday-6-22-2026"),
    "m44": ("-240", "+350", "+650", "FanDuel", "https://www.cbssports.com/soccer/news/argentina-austria-odds-prediction-time-2026-world-cup-picks-best-bets/"),
    "m45": ("-195", "+320", "+600", "Sports Interaction", "https://news.sportsinteraction.com/soccer/fifa-world-cup/story/colombia-vs-dr-congo-odds-prediction-062426-217189"),
    "m46": ("6/1", "3/1", "1/2", "bet365", "https://www.racingpost.com/sport/football-tips/world-cup-2026/panama-vs-croatia-world-cup-prediction-team-news-odds-betting-tips-and-bet-builder-aZnLU5O1Zsqe/"),
    "m47": ("-450", "+550", "+1400", "Sports Interaction", "https://news.sportsinteraction.com/soccer/fifa-world-cup/story/england-vs-ghana-odds-prediction-062326-217179"),
    "m48": ("1/5", "6/1", "11/1", "bet365", "https://www.racingpost.com/sport/football-tips/world-cup-2026/portugal-vs-uzbekistan-world-cup-prediction-team-news-odds-betting-tips-and-bet-builder-a260w1C6DOJl/"),
    "m49": ("19/4", "29/10", "6/10", "bet365", "https://www.racingpost.com/sport/football-tips/world-cup-2026/south-africa-vs-south-korea-world-cup-prediction-team-news-odds-betting-tips-and-bet-builder-afEgA7q1q3rv/"),
    "m50": ("13/5", "3/1", "10/11", "bet365", "https://www.racingpost.com/sport/football-tips/world-cup-2026/czech-republic-vs-mexico-world-cup-prediction-team-news-odds-betting-tips-and-bet-builder-aVhrU9r75F2V/"),
    "m51": ("1/6", "13/2", "14/1", "bet365", "https://www.racingpost.com/sport/football-tips/world-cup-2026/morocco-vs-haiti-world-cup-prediction-team-news-odds-betting-tips-and-bet-builder-ah7S64g5gWZJ/"),
    "m52": ("7/1", "4/1", "4/11", "bet365", "https://www.racingpost.com/sport/football-tips/world-cup-2026/scotland-vs-brazil-world-cup-prediction-team-news-odds-betting-tips-and-bet-builder-a1B9A9D9fjpC/"),
    "m53": ("4/9", "4/1", "21/4", "bet365", "https://www.racingpost.com/sport/football-tips/world-cup-2026/bosnia-and-herzegovina-vs-qatar-betting-tips-predictions-team-news-odds-bet-builder-aIQmi5h5P3A8/"),
    "m54": ("+130", "+220", "+230", "Sports Interaction", "https://news.sportsinteraction.com/soccer/fifa-world-cup/story/switzerland-vs-canada-odds-prediction-062426-217201"),
    "m55": ("+1700", "+700", "-700", "FanDuel", "https://www.foxsports.com/stories/soccer/2026-world-cup-curacao-ivory-coast-odds-prediction-picks"),
    "m59": ("+290", "+320", "-125", "FanDuel", "https://www.foxsports.com/stories/soccer/2026-world-cup-united-states-turkiye-odds-prediction-picks"),  # oriented to team_a=Türkiye
    "m56": ("5/2", "3/1", "19/20", "bet365", "https://www.racingpost.com/sport/football-tips/world-cup-2026/ecuador-vs-germany-world-cup-prediction-team-news-odds-betting-tips-and-bet-builder-aq3YX8o0kQbj/"),
    "m57": ("+100", "+230", "+290", "FanDuel", "https://www.sportsline.com/insiders/japan-vs-sweden-odds-predictions-2026-world-cup-picks-from-proven-soccer-expert/"),
    "m58": ("+2400", "+1011", "-733", "Kalshi", "https://sports.yahoo.com/articles/netherlands-vs-tunisia-predictions-picks-190000498.html"),  # oriented to team_a=Tunisia
    "m60": ("15/8", "23/20", "29/10", "Ladbrokes", "https://www.racingpost.com/sport/football-tips/world-cup-2026/paraguay-vs-australia-world-cup-prediction-team-news-odds-betting-tips-and-bet-builder-a6fxb9K2yEUl/"),
    "m61": ("+1300", "+700", "-556", "BetMGM", "https://www.sportsgambler.com/betting-tips/football/new-zealand-vs-belgium-prediction-lineups-odds-2026-06-26/"),
    "m62": ("29/20", "7/4", "23/10", "Ladbrokes", "https://www.racingpost.com/sport/football-tips/world-cup-2026/egypt-vs-iran-world-cup-prediction-team-news-odds-betting-tips-and-bet-builder-aARLl2s6c96X/"),
    "m63": ("29/20", "5/2", "7/4", "bet365", "https://www.racingpost.com/sport/football-tips/world-cup-2026/cape-verde-vs-saudi-arabia-world-cup-prediction-team-news-odds-betting-tips-and-bet-builder-aSUNw3n9bZIi/"),
    "m64": ("6/1", "31/10", "1/2", "bet365", "https://www.racingpost.com/sport/football-tips/world-cup-2026/uruguay-vs-spain-world-cup-prediction-team-news-odds-betting-tips-and-bet-builder-af11j2h7nZPv/"),
    "m65": ("2/9", "11/2", "11/1", "bet365", "https://www.racingpost.com/sport/football-tips/world-cup-2026/senegal-vs-iraq-world-cup-prediction-team-news-odds-betting-tips-and-bet-builder-abzLt2O2GKan/"),
    "m66": ("7/2", "7/2", "13/20", "Paddy Power", "https://www.racingpost.com/sport/football-tips/world-cup-2026/norway-vs-france-world-cup-prediction-team-news-odds-betting-tips-and-bet-builder-aMxIm1b66uT1/"),
    "m67": ("14/5", "13/10", "9/5", "bet365", "https://www.racingpost.com/sport/football-tips/world-cup-2026/algeria-vs-austria-predictions-team-news-odds-betting-tips-bet-builder-aVgbm2W8srwo/"),
    "m68": ("+1567", "+809", "-614", "Kalshi", "https://www.covers.com/world-cup/argentina-vs-jordan-prediction-picks-odds-saturday-6-27-2026"),  # oriented to team_a=Jordan
    "m69": ("+322", "+280", "-115", "BetOnline", "https://www.vegasodds.com/predictions/soccer/2026-world-cup-group-k-colombia-portugal-preview-odds-predictions-june-27/"),
    "m70": ("-135", "+320", "+330", "Sports Interaction", "https://news.sportsinteraction.com/soccer/fifa-world-cup/story/dr-congo-vs-uzbekistan-odds-prediction-062726-217266"),
    "m71": ("-133", "+218", "+420", "Kalshi", "https://www.covers.com/world-cup/croatia-vs-ghana-prediction-picks-odds-saturday-6-27-2026"),
    "m72": ("12/1", "7/1", "1/6", "bet365", "https://www.racingpost.com/sport/football-tips/world-cup-2026/panama-vs-england-predictions-team-news-odds-betting-tips-bet-builder-apQ9S0K8XqK3/"),
    "m23": ("+135", "+210", "+220", "FanDuel", "https://www.cbssports.com/soccer/news/ghana-panama-odds-prediction-line-time-2026-world-cup-picks-best-bets/"),
    "m38": ("-210", "+310", "+650", "FanDuel", "https://www.foxsports.com/stories/soccer/2026-world-cup-uruguay-cape-verde-odds-prediction-picks"),
}
