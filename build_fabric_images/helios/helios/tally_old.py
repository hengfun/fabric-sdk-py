"""
Test trustee keys
"""

import sys
import os
import json
import utils
from . import algs, electionalgs


def read_json(filename):
    with open(filename) as jsonfile:
        d = json.load(jsonfile)
    return d

def write_json(filename,JSONDict):
    with open(filename,'w') as jsonfile:
        json.dump(JSONDict,jsonfile,indent=4)

filepath = sys.argv[1]
data = read_json(filepath)
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
try: 
        outfile = os.path.join(sys.argv[2],"result.json")
        print("OUTPUT:{}".format(outfile))
        write_json(outfile,{"result":result})
except:
        write_json(os.path.join("result.json"),{"result":result})