import asyncio
import os
from electionalgs import *
from hfc.fabric import Client

loop = asyncio.get_event_loop()

cli = Client(net_profile="test/fixtures/network.json")
org1_admin = cli.get_user(org_name='org1.example.com', name='Admin')
cli.new_channel('businesschannel')
print("Create a New Channel, the response should be true if succeed")

response = loop.run_until_complete(cli.channel_create(
            orderer='orderer.example.com',
            channel_name='businesschannel',
            requestor=org1_admin,
            config_yaml='test/fixtures/e2e_cli/',
            channel_profile='TwoOrgsChannel'
            ))
print(response == True)

print("Join Peers into Channel, the response should be true if succeed")
# try:
responses = loop.run_until_complete(cli.channel_join(
              requestor=org1_admin,
              channel_name='businesschannel',
              peers=['peer0.org1.example.com',
                     'peer1.org1.example.com'],

              orderer='orderer.example.com'
              ))
print(len(responses) == 2)
# except:       


print("Join Peers from a different MSP into Channel")
org2_admin = cli.get_user(org_name='org2.example.com', name='Admin')

# For operations on peers from org2.example.com, org2_admin is required as requestor
responses = loop.run_until_complete(cli.channel_join(
               requestor=org2_admin,
               channel_name='businesschannel',
               peers=['peer0.org2.example.com',
                      'peer1.org2.example.com'],
               orderer='orderer.example.com'
               ))
print(len(responses) == 2)


gopath_bak = os.environ.get('GOPATH', '')
gopath = os.path.normpath(os.path.join(
                      os.path.dirname(os.path.realpath('__file__')),
                      'test/fixtures/chaincode'
                     ))
                     
os.environ['GOPATH'] = os.path.abspath(gopath)

print('Install chain code on Peers in Org1')
responses = loop.run_until_complete(cli.chaincode_install(
               requestor=org1_admin,
               peers=['peer0.org1.example.com',
                      'peer1.org1.example.com'],
               cc_path='github.com/example_cc',
               cc_name='example_c',
               cc_version='v1.0'
               ))

print("Instantiate Chaincode in Channel, the response should be true if succeed")
args = ['a', '200', 'b', '30000000000000000']
# args = [election.election_id,str(election.toJSONDict()),election.election_id,str(election.toJSONDict())]
# args = [str(election.toJSONDict()),'1',str(election.toJSONDict()),'2']
response = loop.run_until_complete(cli.chaincode_instantiate(
               requestor=org1_admin,
               channel_name='businesschannel',
               peers=['peer0.org1.example.com'],
               args=args,
               cc_name='example_c',
               cc_version='v1.0',
               wait_for_event=True # for being sure chaincode is instantiated
               ))

print("Invoke a chaincode in Channel")
args=[election.election_id,str(election.toJSONDict())]
args = ['a', 'b', '1000000000']
# The response should be true if succeed
response = loop.run_until_complete(cli.chaincode_invoke(
               requestor=org1_admin,
               channel_name='businesschannel',
               peers=['peer0.org1.example.com'],
               args=args,
               cc_name='example_cc',
               cc_version='v1.0',
               wait_for_event=True, # for being sure chaincode invocation has been commited in the ledger, default is on tx event
               #cc_pattern='^invoked*' # if you want to wait for chaincode event and you have a `stub.SetEvent("invoked", value)` in your chaincode
               ))

# Query a chaincode
args = ['b']
# The response should be true if succeed
response = loop.run_until_complete(cli.chaincode_query(
               requestor=org1_admin,
               channel_name='businesschannel',
               peers=['peer0.org1.example.com'],
               args=args,
               cc_name='example_cc',
               cc_version='v1.0'
               ))
print(response)

if __name__ == "__main__":
       print('yes')