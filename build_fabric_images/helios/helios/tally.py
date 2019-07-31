"""
Computes results based on output of chaincode, given path to election,factors,bulletinboard
"""

import sys
import os
import json
from helios import utils
from helios import algs, electionalgs


def read_json(filename):
    with open(filename) as jsonfile:
        d = json.load(jsonfile)
    return d

def write_json(filename,JSONDict):
    with open(filename,'w') as jsonfile:
        json.dump(JSONDict,jsonfile,indent=4)
filepath = sys.argv[1]

#read election 
election_dict = read_json(os.path.join(filepath,"election.json"))                                                                                                                                                 

#extract public key
public_key_dict = election_dict['public_key']

#Read Factors
fac = read_json(os.path.join(filepath,"factors.json")) 
factors = [f for f in fac['factors']]

#Parse ballots from BB
bb = read_json(os.path.join(filepath,"bulletin_board.json")) 
ballot_dicts = [ b['Ballot'] for b in bb['bulletinBoard']] 

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