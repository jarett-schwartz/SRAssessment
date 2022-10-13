import pandas as pd
from datetime import datetime
from dateutil.relativedelta import relativedelta

# Read the data from csv's to dataframes
df_competitions = pd.read_csv('./sr_dev_competitions.csv')
df_people = pd.read_csv('./sr_dev_people.csv')
df_stats = pd.read_csv('./sr_dev_stats.csv')
df_teams = pd.read_csv('./sr_dev_teams.csv')

# Get Ronaldo's id and birthdate, filter stats data
ronaldo_id = df_people.loc[df_people['name'] == 'Cristiano Ronaldo']['person_id'].item()
ronaldo_birthdate = datetime.strptime(
    df_people.loc[df_people['name'] == 'Cristiano Ronaldo']['birth_date'].item(),
    "%Y-%m-%d")
df_stats = df_stats[df_stats.person_id == ronaldo_id].drop('person_id', axis=1)

# Get list of club teams, filter stats for club teams, replace team id with team name
club_teams = df_teams[df_teams.team_type == 'club'][['team_id', 'name']]
club_teams = dict(zip(club_teams.team_id, club_teams.name))
club_team_ids = list(club_teams.keys())
df_stats = df_stats[df_stats.team_id.isin(club_team_ids)].replace(club_teams)

# Get list of competitions, replace comp id with comp name
competitions = df_competitions[df_competitions.competition_format == 'league'][['comp_id', 'name']]
competitions = dict(zip(competitions.comp_id, competitions.name))
league_comps = list(competitions.keys())
countries = df_competitions[['name', 'country']]
countries = dict(zip(countries.name, countries.country))
df_stats = df_stats[df_stats.comp_id.isin(league_comps)].replace({'comp_id': competitions})
df_stats['Country'] = df_stats.apply(lambda row: countries[row['comp_id']], axis=1)

# Helper function to get age of player during a season
def getAge(birthdate, season):
    aug1 = datetime(int(season[:4]), 8, 1)
    return relativedelta(aug1, birthdate).years

# Add column with player age on Aug 1 of the season
df_stats['Age'] = df_stats.apply(lambda row: getAge(ronaldo_birthdate, row['season']), axis=1)

# Add column with goals / 90 minutes
df_stats['Goals/90'] = df_stats.apply(lambda row: 90*(row['goals']/row['minutes']), axis=1)

# Rename columns and reorder dataframe
column_names = {
    "season": "Season",
    "comp_id": "Competition",
    "team_id": "Team",
    "games": "Games",
    "minutes": "Minutes",
    "goals": "Goals",
    "assists": "Assists"
}
df_stats.rename(columns=column_names, inplace=True)
df_stats = df_stats[['Season', 'Age', 'Team', 'Country', 'Competition', 'Games', 'Minutes', 'Goals', 'Assists', 'Goals/90']]
df_stats.sort_values(by=['Season', 'Team'], inplace=True)

# Get summary statistics
num_seasons = len(pd.unique(df_stats['Season']))
num_clubs = len(pd.unique(df_stats['Team']))
num_competitions = len(pd.unique(df_stats['Competition']))
num_games = df_stats['Games'].sum()
num_minutes = df_stats['Minutes'].sum()
num_goals = df_stats['Goals'].sum()
num_assists = df_stats['Assists'].sum()
goals_per_90 = 90*(num_goals/num_minutes)
summary_row = pd.Series({
    'Season': f'{num_seasons} Seasons',
    'Age': '',
    'Team': f'{num_clubs} Clubs',
    'Country': '',
    'Competition': f'{num_competitions} Competitions',
    'Games': num_games,
    'Minutes': num_minutes,
    'Goals': num_goals,
    'Assists': num_assists,
    'Goals/90': goals_per_90
})
df_stats = pd.concat([df_stats, summary_row.to_frame().T], ignore_index=True)

# Clean up the dataframe
df_stats['Assists'] = df_stats['Assists'].astype(int)
df_stats['Goals/90'] = df_stats['Goals/90'].astype(float).round(2)
df_stats['Minutes'] = df_stats['Minutes'].map('{:,d}'.format)

if __name__ == '__main__':
    result = df_stats.to_html(index=False)
    f = open("table.html", "w")
    f.write(result)
    f.close()
