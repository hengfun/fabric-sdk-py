# Copyright IBM Corp. 2017 All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
#
import asyncio
import os
import time
import json
import random 
import docker
import logging
import unittest
from helios import electionalgs
from hfc.fabric.channel.channel import SYSTEM_CHANNEL_NAME
from hfc.util.utils import CC_TYPE_GOLANG, package_chaincode
from helios import algs


from hfc.fabric.client import Client
from test.integration.config import E2E_CONFIG
from test.integration.utils import BaseTestCase

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

CC_PATH = 'github.com/election'
CC_NAME = 'election'
CC_VERSION = '2.0'

FIXTURES_PATH = '/home/heng/fabric-sdk-py/test/fixtures/chaincode/src/github.com/election/'


def read_json(path):
    with open(path) as json_file:
        data = json.load(json_file)
    json_data = json.dumps(data)
    return json_data

class E2eTest(BaseTestCase):

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
        self.assertIsNotNone(self.user, 'org1 admin should not be None')

        # Boot up the testing network
        self.shutdown_test_env()
        self.start_test_env()
        time.sleep(1)

    def tearDown(self):
        super(E2eTest, self).tearDown()

    async def channel_create(self):
        """
        Create an channel for further testing.

        :return:
        """
        logger.info("E2E: Channel creation start: name={}".format(
            self.channel_name))

        # By default, self.user is the admin of org1
        node_info = self.network_info['peers']['peer0.org1.example.com']
        set_tls = self.client.set_tls_client_cert_and_key(
            node_info['clientKey']['path'],
            node_info['clientCert']['path']
        )
        self.assertTrue(set_tls)

        response = await self.client.channel_create(
            'orderer.example.com',
            self.channel_name,
            self.user,
            config_yaml=self.config_yaml,
            channel_profile=self.channel_profile)

        self.assertTrue(response)

        logger.info(f"E2E: Channel creation done: name={self.channel_name}")

    async def channel_join(self):
        """
        Join peers of two orgs into an existing channels

        :return:
        """

        logger.info(f"E2E: Channel join start: name={self.channel_name}")

        # channel must already exist when to join
        channel = self.client.get_channel(self.channel_name)
        self.assertIsNotNone(channel)

        orgs = ["org1.example.com", "org2.example.com"]
        for org in orgs:
            org_admin = self.client.get_user(org, 'Admin')

            node_info = self.network_info['peers']['peer0.' + org]
            set_tls = self.client.set_tls_client_cert_and_key(
                node_info['clientKey']['path'],
                node_info['clientCert']['path']
            )
            self.assertTrue(set_tls)

            response = await self.client.channel_join(
                requestor=org_admin,
                channel_name=self.channel_name,
                peers=['peer0.' + org, 'peer1.' + org],
                orderer='orderer.example.com',
            )
            self.assertTrue(response)
            # Verify the ledger exists now in the peer node
            dc = docker.from_env()
            for peer in ['peer0', 'peer1']:
                peer0_container = dc.containers.get(peer + '.' + org)
                code, output = peer0_container.exec_run(
                    'test -f '
                    '/var/hyperledger/production/ledgersData/chains/'
                    f'chains/{self.channel_name}'
                    '/blockfile_000000')
                self.assertEqual(code, 0, "Local ledger not exists")

        logger.info(f"E2E: Channel join done: name={self.channel_name}")

    async def chaincode_install(self):
        """
        Test installing an example chaincode to peer

        :return:
        """
        logger.info("E2E: Chaincode install start")
        cc = f'/var/hyperledger/production/chaincodes/{CC_NAME}.{CC_VERSION}'

        # create packaged chaincode before for having same id
        code_package = package_chaincode(CC_PATH, CC_TYPE_GOLANG)

        orgs = ["org1.example.com", "org2.example.com"]
        for org in orgs:
            org_admin = self.client.get_user(org, "Admin")

            node_info = self.network_info['peers']['peer0.' + org]
            set_tls = self.client.set_tls_client_cert_and_key(
                node_info['clientKey']['path'],
                node_info['clientCert']['path']
            )
            self.assertTrue(set_tls)

            responses = await self.client.chaincode_install(
                requestor=org_admin,
                peers=['peer0.' + org, 'peer1.' + org],
                cc_path=CC_PATH,
                cc_name=CC_NAME,
                cc_version=CC_VERSION,
                packaged_cc=code_package
            )
            self.assertTrue(responses)
            # Verify the cc pack exists now in the peer node
            dc = docker.from_env()
            for peer in ['peer0', 'peer1']:
                peer_container = dc.containers.get(peer + '.' + org)
                code, output = peer_container.exec_run(f'test -f {cc}')
                self.assertEqual(code, 0, "chaincodes pack not exists")

        logger.info("E2E: chaincode install done")

    def generate_keys(self):
        ELGAMAL_PARAMS = algs.ElGamal()
        ELGAMAL_PARAMS.p = 16328632084933010002384055033805457329601614771185955389739167309086214800406465799038583634953752941675645562182498120750264980492381375579367675648771293800310370964745767014243638518442553823973482995267304044326777047662957480269391322789378384619428596446446984694306187644767462460965622580087564339212631775817895958409016676398975671266179637898557687317076177218843233150695157881061257053019133078545928983562221396313169622475509818442661047018436264806901023966236718367204710755935899013750306107738002364137917426595737403871114187750804346564731250609196846638183903982387884578266136503697493474682071
        ELGAMAL_PARAMS.q = 61329566248342901292543872769978950870633559608669337131139375508370458778917
        ELGAMAL_PARAMS.g = 14887492224963187634282421537186040801304008017743492304481737382571933937568724473847106029915040150784031882206090286938661464458896494215273989547889201144857352611058572236578734319505128042602372864570426550855201448111746579871811249114781674309062693442442368697449970648232621880001709535143047913661432883287150003429802392229361583608686643243349727791976247247948618930423866180410558458272606627111270040091203073580238905303994472202930783207472394578498507764703191288249547659899997131166130259700604433891232298182348403175947450284433411265966789131024573629546048637848902243503970966798589660808533
        self.kp_1 = ELGAMAL_PARAMS.generate_keypair()
        self.kp_2 = ELGAMAL_PARAMS.generate_keypair()
        self.kp_3 = ELGAMAL_PARAMS.generate_keypair()
        self.full_pk = self.kp_1.pk*self.kp_2.pk*self.kp_3.pk

    async def setupElection(self):
        """
        Test instantiating an example chaincode to peer

        :return:
        """

        org = "org1.example.com"
        # args = ['a', '200', 'b', '300']
        election_json = read_json(os.path.join(FIXTURES_PATH,'election.json'))

        # generate key pair
        self.generate_keys()

        #update json with new public key
        election_dict = json.loads(election_json)['election']
        election_dict['public_key'] = self.full_pk.toJSONDict()
        election_json = json.dumps(election_dict)

        voting_json = read_json(os.path.join(FIXTURES_PATH, 'voting_list.json'))
        trustee_json = read_json(os.path.join(FIXTURES_PATH, 'trustee_list.json'))
        
        args = [election_json,voting_json,trustee_json]
        policy = {
            'identities': [
                {'role': {'name': 'member', 'mspId': 'Org1MSP'}},
                # {'role': {'name': 'admin', 'mspId': 'Org1MSP'}},
            ],
            'policy': {
                '1-of': [
                    {'signed-by': 0},
                    # {'signed-by': 1},
                ]
            }
        }
        org_admin = self.client.get_user(org, "Admin")

        node_info = self.network_info['peers']['peer0.' + org]
        set_tls = self.client.set_tls_client_cert_and_key(
            node_info['clientKey']['path'],
            node_info['clientCert']['path']
        )
        self.assertTrue(set_tls)

        response = await self.client.chaincode_instantiate(
            requestor=org_admin,
            channel_name=self.channel_name,
            peers=['peer0.' + org],
            args=args,
            cc_name=CC_NAME,
            cc_version=CC_VERSION,
            cc_endorsement_policy=policy,
            wait_for_event=True
        )
        logger.info(
            "E2E: Chaincode instantiation response {}".format(response))
        policy = {
            'version': 0,
            'rule': {'n_out_of': {
                'n': 1,
                'rules': [
                    {'signed_by': 0},
                    # {'signed_by': 1}
                ]}
            },
            'identities': [
                {
                    'principal_classification': 'ROLE',
                    'principal': {
                        'msp_identifier': 'Org1MSP',
                        'role': 'MEMBER'
                    }
                },
                # {
                #     'principal_classification': 'ROLE',
                #     'principal': {
                #         'msp_identifier': 'Org1MSP',
                #         'role': 'ADMIN'
                #     }
                # },
            ]
        }
        self.assertEqual(response['name'], CC_NAME)
        self.assertEqual(response['version'], CC_VERSION)
        self.assertEqual(response['policy'], policy)

    async def getBallot(self):
        """
        Test invoking an example chaincode to peer

        :return:
        """

        orgs = ["org1.example.com"]
        args = ['']
        for org in orgs:
            org_admin = self.client.get_user(org, "Admin")

            node_info = self.network_info['peers']['peer0.' + org]
            set_tls = self.client.set_tls_client_cert_and_key(
                node_info['clientKey']['path'],
                node_info['clientCert']['path']
            )
            self.assertTrue(set_tls)

            response = await self.client.chaincode_invoke(
                requestor=org_admin,
                channel_name=self.channel_name,
                peers=['peer1.' + org],
                args=args, fcn="get_ballot",
                cc_name=CC_NAME,
                wait_for_event=True,
                cc_pattern="^invoked*"  # for chaincode event
            )
        json_dict = json.loads(response)
        self.election = electionalgs.Election.fromJSONDict(json_dict)

    async def submitBallot(self,voterid):
        """
        Test invoking an example chaincode to peer

        :return:
        """
        orgs = ["org1.example.com"]
        
        for org in orgs:
            org_admin = self.client.get_user(org, "Admin")

            node_info = self.network_info['peers']['peer0.' + org]
            set_tls = self.client.set_tls_client_cert_and_key(
                node_info['clientKey']['path'],
                node_info['clientCert']['path']
            )
            self.assertTrue(set_tls)

            answers = []
            for question in self.election.questions:

                # answers.append(input(q['question']))
                answers.append([random.randint(0, len(self.election.questions))])
            ballot= electionalgs.EncryptedVote.fromElectionAndAnswers(
                self.election, answers)
            ballot_dict = ballot.toJSONDict()
            ballotJSON = json.dumps(ballot_dict)
            args = [voterid, ballotJSON]


            response = await self.client.chaincode_invoke(
                requestor=org_admin,
                channel_name=self.channel_name,
                peers=['peer1.' + org],
                args=args, fcn="submit_ballot",
                cc_name=CC_NAME,
                wait_for_event=True,
                cc_pattern="^invoked*"  # for chaincode event
            )
        logger.info("Ballot submitted")

    async def getBulletinBoard(self):
        """
        Test invoking an example chaincode to peer
        :return:
        """

        orgs = ["org1.example.com"]
        args = ['']
        for org in orgs:
            org_admin = self.client.get_user(org, "Admin")

            node_info = self.network_info['peers']['peer0.' + org]
            set_tls = self.client.set_tls_client_cert_and_key(
                node_info['clientKey']['path'],
                node_info['clientCert']['path']
            )
            self.assertTrue(set_tls)
           

            response = await self.client.chaincode_invoke(
                requestor=org_admin,
                channel_name=self.channel_name,
                peers=['peer1.' + org],
                args=args, fcn="get_bulletin_board",
                cc_name=CC_NAME,
                wait_for_event=True,
                cc_pattern="^invoked*"  # for chaincode event
            )
        # print(response)
        self.bulletinBoard = json.loads(response)['bulletinBoard']
        self.ballots = [b["Ballot"] for b in self.bulletinBoard]
        self.encryptedBallots = [electionalgs.EncryptedVote.fromJSONDict(b) for b in self.ballots]
        self.tally = self.election.init_tally()
        self.tally.add_vote_batch(self.encryptedBallots)
        logger.info("get bulletinboard")

    async def submitFactor(self,trustee,sk):
        """
        Test invoking an example chaincode to peer
        :return:
        """

        orgs = ["org1.example.com"]

        for org in orgs:
            org_admin = self.client.get_user(org, "Admin")

            node_info = self.network_info['peers']['peer0.' + org]
            set_tls = self.client.set_tls_client_cert_and_key(
                node_info['clientKey']['path'],
                node_info['clientCert']['path']
            )
            self.assertTrue(set_tls)
            factor, proof = self.tally.decryption_factors_and_proofs(
                sk)
            factor_json = json.dumps(factor)
            proof_json = json.dumps(proof)
            args = [trustee,factor_json,trustee+"proof",proof_json]
            response = await self.client.chaincode_invoke(
                requestor=org_admin,
                channel_name=self.channel_name,
                peers=['peer1.' + org],
                args=args, fcn="submit_decryption_factor",
                cc_name=CC_NAME,
                wait_for_event=True,
                cc_pattern="^invoked*"  # for chaincode event
            )
        logger.info("submit factor")

    async def startTally(self):
        """
        Test invoking an example chaincode to peer
        :return:
        """

        orgs = ["org1.example.com"]
        args = ['']
        for org in orgs:
            org_admin = self.client.get_user(org, "Admin")

            node_info = self.network_info['peers']['peer0.' + org]
            set_tls = self.client.set_tls_client_cert_and_key(
                node_info['clientKey']['path'],
                node_info['clientCert']['path']
            )
            self.assertTrue(set_tls)

            response = await self.client.chaincode_invoke(
                requestor=org_admin,
                channel_name=self.channel_name,
                peers=['peer1.' + org],
                args=args, fcn="start_tally",
                cc_name=CC_NAME,
                wait_for_event=True,
                cc_pattern="^invoked*"  # for chaincode event
            )
            print(response)
        logger.info("tally completed")

    async def getResult(self):
        """
        Test invoking an example chaincode to peer

        :return:
        """
        print("voter query result")
        orgs = ["org1.example.com"]
        args = ['']
        for org in orgs:
            org_admin = self.client.get_user(org, "Admin")

            node_info = self.network_info['peers']['peer0.' + org]
            set_tls = self.client.set_tls_client_cert_and_key(
                node_info['clientKey']['path'],
                node_info['clientCert']['path']
            )
            self.assertTrue(set_tls)

            response = await self.client.chaincode_invoke(
                requestor=org_admin,
                channel_name=self.channel_name,
                peers=['peer1.' + org],
                args=args, fcn="get_result",
                cc_name=CC_NAME,
                wait_for_event=False,
                cc_pattern="^invoked*"  # for chaincode event
            )
        print(response)

    def test_in_sequence(self):

        loop = asyncio.get_event_loop()

        logger.info("\n\nElection testing started...")
        """ Setup Blockchain"""
        self.client.new_channel(SYSTEM_CHANNEL_NAME)
        loop.run_until_complete(self.channel_create())
        loop.run_until_complete(self.channel_join())
        loop.run_until_complete(self.chaincode_install())

        """ Election"""
        loop.run_until_complete(self.setupElection())
        loop.run_until_complete(self.getBallot())
        loop.run_until_complete(self.submitBallot("voter1"))
        loop.run_until_complete(self.submitBallot("voter2"))
        loop.run_until_complete(self.submitBallot("voter3"))
        loop.run_until_complete(self.getBulletinBoard())
        loop.run_until_complete(self.submitFactor("trustee1", self.kp_1.sk))
        loop.run_until_complete(self.submitFactor("trustee2", self.kp_2.sk))
        loop.run_until_complete(self.submitFactor("trustee3", self.kp_3.sk))
        loop.run_until_complete(self.startTally())
        loop.run_until_complete(self.getResult())

        logger.info("Election all test cases done\n\n")


if __name__ == "__main__":
    unittest.main()
