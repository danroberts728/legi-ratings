""" legi-ratings.py

This script assigns a number and letter grade to legislators in states based on specified
votes. It uses the Open States API for records.

Example:
    $ python legi-ratings.py input_file.txt

Todo:
    * upper and lower legislators should go to separate files or a single excel file
    * currently the script writes all votes for each chamber, so house votes are listed in the senate list. This
        should be corrected so that only house votes are listed in the house and senate votes in the senate. A current
        workaroud is to just remove the extra votes

Required Modules:
    * pyopenstates
    * os.path
    * sys

Author:
    * Dan Roberts droberts@albeer.org

License:
    * MIT
"""

import os.path
import sys
import config
import pyopenstates as osClient

def GetLegislators(state, chamber):
    """
        Args:
            state (str): two-letter state string for Open State lookup
            chamber (str): Open States chamber string, should be 'lower' or 'upper'
        Returns:
            list: A lsit of legislator-dictionaries with incumbent information for the
                state and chamber.
    """
    legislators = osClient.search_legislators(state=state, chamber=chamber, active=True)
    legislator_list = []
    for l in legislators:
        legislator_list.append({
        'leg_id': l['leg_id'],
        'name': l['full_name'],
        'first_name':l['first_name'],
        'last_name': l['last_name'],
        'party': l['party'],
        'district': l['district'],
        'all_ids': l['all_ids'],
        'votes': {}
        })
    return legislator_list;

def AddVotes(legislators, vote_data):
    """
        Args:
            legislators (list): Pre-populated legislator information
            vote_data (obj): Open States vote object
        Returns:
            list: Returns the legislators parameter but populated with the vote records
    """
    for l in legislators:
        if next( (x for x in vote_data['yes_votes'] if x['leg_id'] in l['all_ids']), None ) is not None:
            l['votes'][vote_data['vote_id']] = 'Y'
        elif next( (x for x in vote_data['no_votes'] if x['leg_id'] in l['all_ids']), None ) is not None:
            l['votes'][vote_data['vote_id']] = 'N'
        else:
            l['votes'][vote_data['vote_id']] = 'O'
    return legislators

def WriteVotes(legislators):
    """
        Args:
            legislators (list): Pre-populated legislator information with voting records
        Returns:
            str: a comma-delimited set of lines for writing a CSV file with legislator information,
                votes, and scoring
    """
    lines = ''
    for leg in legislators:
        total_right = 0
        total_possible = 0
        line = leg['district'] + ',' + leg['name'] + ',' + leg['party']
        for v in tracked_votes:
            vote_id = v['vote_id']
            vote_pref = v['vote_preference']
            vote_weight = v['vote_weight']
            vote_cast = 'NA'
            if vote_id in leg['votes']:
                vote_cast = leg['votes'][vote_id]
            line += "," + vote_cast

            if vote_cast == 'Y' or vote_cast == 'N' or vote_cast == vote_pref:
                total_possible += int(vote_weight)
            if vote_cast == vote_pref:
                total_right += int(vote_weight)
        if total_possible == 0:
            score = '-'
        else:
            score = round(total_right / float(total_possible),3)
        
        lines = line + ',' + str(score) + ',' + str(letter_score) + '\n')
    return lines

# Main:
# Validate input
if len(sys.argv) < 2:
    raise ValueError("Must provide input file as argument in command line")
input_file = sys.argv[1]
if not os.path.isfile(input_file):
    raise ValueError("Input file does not exist: " + input_file)

# Setup Open States API Client
osClient.set_api_key(config.openstates_api_key)

upper_legislators = GetLegislators(state=config.state, chamber='upper')
lower_legislators = GetLegislators(state=config.state, chamber='lower')

tracked_votes = []
for line in open(input_file):
    if line.startswith('#'):
        continue
    input_vote_info = line.strip('\n\r').split(',')
    tracked_votes.append({
        'vote_session' : input_vote_info[0],
        'vote_bill_no' : input_vote_info[1],
        'vote_id' : input_vote_info[2],
        'vote_preference' : input_vote_info[3],
        'vote_weight' : input_vote_info[4]
    })

for vote in tracked_votes:
    all_votes_data = osClient.get_bill(state=config.state, term=vote['vote_session'], bill_id=vote['vote_bill_no'], fields='votes')['votes']
    tracked_vote_data = next( (x for x in all_votes_data if x['id'] == vote['vote_id']), None )
    if tracked_vote_data['chamber'] == 'upper':
        upper_legislators = AddVotes(upper_legislators, tracked_vote_data)
    if tracked_vote_data['chamber'] == 'lower':
        lower_legislators = AddVotes(lower_legislators, tracked_vote_data)

export_fh = open('output.csv', 'w')
export_fh.write('Upper' + '\n')
header_line = 'SD,Name,Party'
for v in tracked_votes:
    header_line += "," + v['vote_bill_no'] + " (" + v['vote_session'] + ")"

export_fh.write(header_line + '\n')
export_fth.write( WriteVotes(upper_legislators) )

export_fh.write('Lower' + '\n')
header_line = 'HD,Name,Party'
for v in tracked_votes:
    header_line += "," + v['vote_bill_no'] + " (" + v['vote_session'] + ")"

export_fh.write(header_line + '\n')
export_fth.write( WriteVotes(lower_legislators) )
            