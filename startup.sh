docker rm -f $(docker ps -a -q)

HLF_VERSION=1.4.0
docker pull hyperledger/fabric-peer:${HLF_VERSION}
docker pull hyperledger/fabric-orderer:${HLF_VERSION}
docker pull hyperledger/fabric-ca:${HLF_VERSION}
docker pull hyperledger/fabric-ccenv:${HLF_VERSION}
docker-compose -f test/fixtures/docker-compose-2orgs-4peers-tls.yaml up