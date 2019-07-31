"""
Test trustee keys
"""

import sys
import os
import json
# from algs import *
import utils
from . import algs, electionalgs


def read_json(filename):
    with open(filename) as jsonfile:
        d = json.load(jsonfile)
    return d

def write_json(filename,JSONDict):
    with open(filename,'w') as jsonfile:
        json.dump(JSONDict,jsonfile,indent=4)

filename = sys.argv[1]

data = read_json(filename)
factors = data['factors']
election_dict = data['election']
ballot_dicts = data['ballots']
public_key_dict = data['election']['public_key']

ballots = [electionalgs.EncryptedVote.fromJSONDict(b) for b in ballot_dicts]

election = electionalgs.Election.fromJSONDict(election_dict)
pk =algs.EGPublicKey()
pk = pk.fromJSONDict(public_key_dict)

tally = election.init_tally()
tally.add_vote_batch(ballots)
result = tally.decrypt_from_factors(factors,pk)
# print(result)

# if __name__ == "__main__":
#    filename = sys.argv[1]