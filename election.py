# Copyright O Corp. 2019 All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
#

import os
import json
from test.integration.config import E2E_CONFIG
import asyncio
import time
import subprocess
from hfc.fabric import Client

CONNECTION_PROFILE_PATH = 'test/fixtures/network.json'
CONFIG_YAML_PATH = 'test/fixtures/e2e_cli/'
CHAINCODE_PATH = 'test/fixtures/chaincode'


class Election(object):
    def __init__(self):
        self.r = 0

    def setUp(self):
        self.gopath_bak = os.environ.get('GOPATH', '')
        gopath = os.path.normpath(os.path.join(os.path.dirname(__file__),
                                                "../fixtures/chaincode"))
        os.environ['GOPATH'] = os.path.abspath(gopath)
        self.channel_tx = \
            E2E_CONFIG['test-network']['channel-artifacts']['channel.tx']
        self.compose_file_path = \
            E2E_CONFIG['test-network']['docker']['compose_file_mutual_tls']

        self.config_yaml = \
            E2E_CONFIG['test-network']['channel-artifacts']['config_yaml']
        self.channel_profile = \
            E2E_CONFIG['test-network']['channel-artifacts']['channel_profile']
        self.client = Client('test/fixtures/network-mutual-tls.json')

        with open('test/fixtures/network-mutual-tls.json') as f:
            self.network_info = json.load(f)

        self.channel_name = "businesschannel"  # default application channel
        self.user = self.client.get_user('org1.example.com', 'Admin')
        # self.assertIsNotNone(self.user, 'org1 admin should not be None')

        # Boot up the testing network
        self.shutdown_test_env()
        self.start_test_env()
        time.sleep(1)

    def tearDown(self):
        time.sleep(1)
        self.shutdown_test_env()

    def start_test_env(self):
        self.cli_call(["docker-compose", "-f", self.compose_file_path, "up", "-d"])

    def shutdown_test_env(self):
        self.cli_call(["docker-compose", "-f", self.compose_file_path, "down"])

    def check_logs(self):
        self.cli_call(["docker-compose", "-f", self.compose_file_path, "logs",
                       "--tail=200"])
    def cli_call(self,arg_list, expect_success=True, env=os.environ.copy()):
        """Executes a CLI command in a subprocess and return the results.

        Args:
            arg_list: a list command arguments
            expect_success: use False to return even if an error occurred
                            when executing the command
            env:

        Returns: (string, string, int) output message, error message, return code

        """
        p = subprocess.Popen(arg_list, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, env=env)
        output, error = p.communicate()
        if p.returncode != 0:
            if output:
                print("Output:\n" + str(output))
            if error:
                print("Error Message:\n" + str(error))
            if expect_success:
                raise subprocess.CalledProcessError(
                    p.returncode, arg_list, output)
        return output, error, p.returncode


if __name__ == "__main__":
    a = Election()
    # a.setUp()
    # b = input('yo')
    # print(b)
    # loop = asyncio.get_event_loop()

    # cli = Client(net_profile="test/fixtures/network.json")
    # org1_admin = cli.get_user(org_name='org1.example.com', name='Admin')

    # # Create a New Channel, the response should be true if succeed
    # response = loop.run_until_complete(cli.channel_create(
    #     orderer='orderer.example.com',
    #     channel_name='businesschannel',
    #     requestor=org1_admin,
    #     config_yaml='test/fixtures/e2e_cli/',
    #     channel_profile='TwoOrgsChannel'
    # ))
    # print(response == True)

    # # Join Peers into Channel, the response should be true if succeed
    # orderer_admin = cli.get_user(org_name='orderer.example.com', name='Admin')
    # responses = loop.run_until_complete(cli.channel_join(
    #     requestor=org1_admin,
    #     channel_name='businesschannel',
    #     peers=['peer0.org1.example.com',
    #         'peer1.org1.example.com'],

    #     orderer='orderer.example.com'
    # ))
    # print(len(responses) == 2)


    # # Join Peers from a different MSP into Channel
    # org2_admin = cli.get_user(org_name='org2.example.com', name='Admin')

    # # For operations on peers from org2.example.com, org2_admin is required as requestor
    # responses = loop.run_until_complete(cli.channel_join(
    #     requestor=org2_admin,
    #     channel_name='businesschannel',
    #     peers=['peer0.org2.example.com',
    #         'peer1.org2.example.com'],
    #     orderer='orderer.example.com'
    # ))
    # print(len(responses) == 2)

    # gopath_bak = os.environ.get('GOPATH', '')
    # gopath = os.path.normpath(os.path.join(
    #     os.path.dirname(os.path.realpath('__file__')),
    #     'test/fixtures/chaincode'
    # ))
    # os.environ['GOPATH'] = os.path.abspath(gopath)

    # # The response should be true if succeed
    # responses = loop.run_until_complete(cli.chaincode_install(
    #     requestor=org1_admin,
    #     peers=['peer0.org1.example.com',
    #         'peer1.org1.example.com'],
    #     cc_path='github.com/example_cc',
    #     cc_name='example_cc',
    #     cc_version='v1.0'
    # ))

    # # Instantiate Chaincode in Channel, the response should be true if succeed
    # args = ['a', '200', 'b', '300']

    # # policy, see https://hyperledger-fabric.readthedocs.io/en/release-1.4/endorsement-policies.html
    # policy = {
    #     'identities': [
    #         {'role': {'name': 'member', 'mspId': 'Org1MSP'}},
    #     ],
    #     'policy': {
    #         '1-of': [
    #             {'signed-by': 0},
    #         ]
    #     }
    # }
    # response = loop.run_until_complete(cli.chaincode_instantiate(
    #     requestor=org1_admin,
    #     channel_name='businesschannel',
    #     peers=['peer0.org1.example.com'],
    #     args=args,
    #     cc_name='example_cc',
    #     cc_version='v1.0',
    #     cc_endorsement_policy=policy,  # optional, but recommended
    #     collections_config=None,  # optional, for private data policy
    #     transient_map=None,  # optional, for private data
    #     wait_for_event=True  # optional, for being sure chaincode is instantiated
    # ))

    # # Invoke a chaincode
    # args = ['a', 'b', '100']
    # # The response should be true if succeed
    # response = loop.run_until_complete(cli.chaincode_invoke(
    #     requestor=org1_admin,
    #     channel_name='businesschannel',
    #     peers=['peer0.org1.example.com'],
    #     args=args,
    #     cc_name='example_cc',
    #     transient_map=None,  # optional, for private data
    #     # for being sure chaincode invocation has been commited in the ledger, default is on tx event
    #     wait_for_event=True,
    #     #cc_pattern='^invoked*' # if you want to wait for chaincode event and you have a `stub.SetEvent("invoked", value)` in your chaincode
    # ))

    # # Query a chaincode
    # args = ['b']
    # # The response should be true if succeed
    # response = loop.run_until_complete(cli.chaincode_query(
    #     requestor=org1_admin,
    #     channel_name='businesschannel',
    #     peers=['peer0.org1.example.com'],
    #     args=args,
    #     cc_name='example_cc'
    # ))

    # # Upgrade a chaincode
    # # policy, see https://hyperledger-fabric.readthedocs.io/en/release-1.4/endorsement-policies.html
    # policy = {
    #     'identities': [
    #         {'role': {'name': 'member', 'mspId': 'Org1MSP'}},
    #         {'role': {'name': 'admin', 'mspId': 'Org1MSP'}},
    #     ],
    #     'policy': {
    #         '1-of': [
    #             {'signed-by': 0}, {'signed-by': 1},
    #         ]
    #     }
    # }
    # response = loop.run_until_complete(cli.chaincode_upgrade(
    #     requestor=org1_admin,
    #     channel_name='businesschannel',
    #     peers=['peer0.org1.example.com'],
    #     args=args,
    #     cc_name='example_cc',
    #     cc_version='v1.0',
    #     cc_endorsement_policy=policy,  # optional, but recommended
    #     collections_config=None,  # optional, for private data policy
    #     transient_map=None,  # optional, for private data
    #     wait_for_event=True  # optional, for being sure chaincode is instantiated
    # ))
