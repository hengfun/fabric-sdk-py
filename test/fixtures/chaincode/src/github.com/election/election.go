/*
 * Copyright IBM Corp All Rights Reserved
 *
 * SPDX-License-Identifier: Apache-2.0
 */

package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io/ioutil"
	"os"
	"os/exec"
	"github.com/hyperledger/fabric/core/chaincode/shim"
	"github.com/hyperledger/fabric/protos/peer"
)

// heliosElection implements a simple chaincode to manage an asset
type heliosElection struct {
}

type Election struct {
	VotingEndsAt interface{} `json:"voting_ends_at"`
	PublicKey    struct {
		Y string `json:"y"`
		P string `json:"p"`
		Q string `json:"q"`
		G string `json:"g"`
	} `json:"public_key"`
	BallotType string `json:"ballot_type"`
	Name       string `json:"name"`
	Questions  []struct {
		Max       int      `json:"max"`
		Question  string   `json:"question"`
		ShortName string   `json:"short_name"`
		Answers   []string `json:"answers"`
		Min       int      `json:"min"`
	} `json:"questions"`
	TallyType      string      `json:"tally_type"`
	VotingStartsAt interface{} `json:"voting_starts_at"`
	VotersHash     interface{} `json:"voters_hash"`
	ElectionID     string      `json:"election_id"`
}

type Ballot struct {
	ElectionID   string `json:"election_id"`
	ElectionHash string `json:"election_hash"`
	Answers      []struct {
		IndividualProofs [][]struct {
			Challenge  string `json:"challenge"`
			Commitment struct {
				A string `json:"A"`
				B string `json:"B"`
			} `json:"commitment"`
			Response string `json:"response"`
		} `json:"individual_proofs"`
		OverallProof []struct {
			Challenge  string `json:"challenge"`
			Commitment struct {
				A string `json:"A"`
				B string `json:"B"`
			} `json:"commitment"`
			Response string `json:"response"`
		} `json:"overall_proof"`
		Choices []struct {
			Alpha string `json:"alpha"`
			Beta  string `json:"beta"`
		} `json:"choices"`
	} `json:"answers"`
}

type VotingList struct {
	Voters []string `json:"voters"`
}

type TrusteeList struct {
	Trustee []string `json:"trustee"`
}

type Factor struct {
	Factor [][]string `json:"factor"`
}

func prepare_bulletin_board(stub shim.ChaincodeStubInterface, args []byte) {
	votingbyteValue := args
	var votinglist VotingList
	json.Unmarshal(votingbyteValue, &votinglist)
	stub.PutState("voting_list", []byte(string(votingbyteValue)))
	i := 0
	for i < len(votinglist.Voters) {
		err := stub.PutState(votinglist.Voters[i], []byte(string("empty")))
		if err != nil {
			fmt.Println(err)
		}
		i = i + 1
	}
}
func prepare_trustee(stub shim.ChaincodeStubInterface, args []byte) {
	trusteebyteValue := args
	var trusteelist TrusteeList
	json.Unmarshal(trusteebyteValue, &trusteelist)
	stub.PutState("trustee_list", []byte(string(trusteebyteValue)))
	j := 0
	for j < len(trusteelist.Trustee) {
		err := stub.PutState(trusteelist.Trustee[j], []byte(string("empty")))
		if err != nil {
			fmt.Println(err)
		}
		j = j + 1
	}
}

func (t *heliosElection) Init(stub shim.ChaincodeStubInterface) peer.Response {
	// prepares ledger for election,
	// takes in Election, VotingList, TrusteeList
	fmt.Println("Setup Election")
	_, args := stub.GetFunctionAndParameters()
	var electionJSON, votingListJSON, trusteeListJSON string
	electionJSON = args[0]
	votingListJSON = args[1]
	trusteeListJSON = args[2]
	fmt.Println(electionJSON)
	fmt.Println(votingListJSON)

	//put election parameters onto leder
	stub.PutState("election", []byte(electionJSON))
	//prepare ledger for each voter, put voters list on ledger
	prepare_bulletin_board(stub, []byte(votingListJSON))
	//prepare ledger for each trustee, put trustee list on ledger
	prepare_trustee(stub, []byte(trusteeListJSON))
	stub.SetEvent("init", []byte(electionJSON))
	return shim.Success(nil)
}

func (t *heliosElection) Invoke(stub shim.ChaincodeStubInterface) peer.Response {
	// Extract the function and args from the transaction proposal
	fn, args := stub.GetFunctionAndParameters()

	var result string
	// var result2 byte
	var err error
	if fn == "set" {
		result, err = set(stub, args)
	} else if fn == "get_ballot" {
		result, err = get_ballot(stub)
	} else if fn == "submit_ballot" {
		result, err = submit_ballot(stub, args)
	} else if fn == "get_bulletin_board" {
		result, err = get_bulletin_board(stub)
	} else if fn == "submit_decryption_factor" {
		result, err = submit_decryption_factor(stub, args)
	} else if fn == "start_tally" {
		result, err = start_tally(stub)
	} else if fn == "get_result" {
		result, err = get_result(stub)
	} else { // assume 'get' even if fn is nil
		result, err = get(stub, args)
	}
	if err != nil {
		return shim.Error(err.Error())
	}
	// Return the result as success payload
	return shim.Success([]byte(result))
}

func submit_ballot(stub shim.ChaincodeStubInterface, args []string) (string, error) {
	fmt.Println("Submit ballot")
	var voterid, ballot string
	voterid = args[0]
	ballot = args[1]
	ballotBytes := []byte(ballot)
	stub.PutState(voterid, ballotBytes)
	stub.SetEvent("invoked", ballotBytes)
	return string("sucessful"), nil
}

func get_ballot(stub shim.ChaincodeStubInterface) (string, error) {
	fmt.Println("Get ballot")
	electionbyteValue, _ := stub.GetState("election")
	stub.SetEvent("invoked", electionbyteValue)
	return string(electionbyteValue), nil
}

func get_bulletin_board(stub shim.ChaincodeStubInterface) (string, error) {
	// Gets voting list from ledger, returns ballot for each voter
	fmt.Println("Get bulletin board")

	// Get Voting list
	votingbyteValue, _ := stub.GetState("voting_list")
	fmt.Println(string(votingbyteValue))
	var votinglist VotingList
	json.Unmarshal(votingbyteValue, &votinglist)

	// Create Buffer
	var buffer bytes.Buffer
	buffer.Write([]byte(`{"bulletinBoard":`))
	buffer.Write([]byte("["))
	i := 0
	bArrayMemberAlreadyWritten := false
	// For each voter append voter, and ballot to ballot_list
	for i < len(votinglist.Voters) {
		fmt.Println(votinglist.Voters[i])
		if bArrayMemberAlreadyWritten == true {
			buffer.Write([]byte(","))
		}

		ballotbyteValue, _ := stub.GetState(votinglist.Voters[i])
		buffer.Write([]byte(`{"Voter":"`))
		buffer.Write([]byte(votinglist.Voters[i]))
		buffer.Write([]byte(`","Ballot":`))
		buffer.Write([]byte(string(ballotbyteValue)))
		buffer.Write([]byte(`}`))

		bArrayMemberAlreadyWritten = true
		i = i + 1
	}

	buffer.Write([]byte("]"))
	buffer.Write([]byte("} "))

	var v interface{}
	json.Unmarshal(buffer.Bytes(), &v)
	BulletinBoardJSON, _ := json.MarshalIndent(v, "", " ")
	_ = ioutil.WriteFile("/helios/bulletin_board.json", BulletinBoardJSON, 0644)
	stub.SetEvent("invoked", buffer.Bytes())

	return buffer.String(), nil
}

func submit_decryption_factor(stub shim.ChaincodeStubInterface, args []string) (string, error) {
	fmt.Println("Submit decryption factor")
	var trustee, factor, trusteeProofKey, proof string
	trustee = args[0]
	factor = args[1]
	// key for to place trustee proof
	trusteeProofKey = args[2]
	proof = args[3]
	factorBytes := []byte(factor)
	proofBytes := []byte(proof)
	stub.PutState(trustee, factorBytes)
	stub.PutState(trusteeProofKey, proofBytes)
	stub.SetEvent("invoked", factorBytes)
	return string("sucessful"), nil
}

func check_factors(stub shim.ChaincodeStubInterface) (bool, int) {
	fmt.Println("Check all factors submitted")
	// check if all factors submited
	trusteebyteValue, _ := stub.GetState("trustee_list")
	var trusteelist TrusteeList
	json.Unmarshal(trusteebyteValue, &trusteelist)
	j := 0
	k := 0
	election_finished := false
	for j < len(trusteelist.Trustee) {
		factorAsbytes, _ := stub.GetState(trusteelist.Trustee[j])
		if "empty" != string(factorAsbytes) {
			k = k + 1
		}
		j = j + 1
	}
	if k == len(trusteelist.Trustee) {
		election_finished = true
	}
	return election_finished, k
}

func get_all_factors(stub shim.ChaincodeStubInterface) bytes.Buffer {
	fmt.Println("Get factors")
	trusteebyteValue, _ := stub.GetState("trustee_list")
	var trusteelist TrusteeList
	json.Unmarshal(trusteebyteValue, &trusteelist)
	i := 0
	var buffer bytes.Buffer
	buffer.Write([]byte(`{"factors":`))
	buffer.Write([]byte("["))
	for i < len(trusteelist.Trustee) {
		fmt.Println(trusteelist.Trustee[i])
		factorbyteValue, _ := stub.GetState(trusteelist.Trustee[i])
		buffer.Write(factorbyteValue)
		i = i + 1
		if i < len(trusteelist.Trustee) {
			buffer.Write([]byte(","))
		}
	}
	buffer.Write([]byte("]"))
	buffer.Write([]byte("}"))
	var v interface{}
	json.Unmarshal(buffer.Bytes(), &v)
	// fmt.Printf(buffer.String())
	factorsJSON, _ := json.MarshalIndent(v, "", " ")
	// fmt.Println(v)
	err2 := ioutil.WriteFile("/helios/factors.json", factorsJSON, 0644)
	fmt.Println(err2)
	stub.SetEvent("invoked", buffer.Bytes())
	return buffer
}

func start_tally(stub shim.ChaincodeStubInterface) (string, error) {
	fmt.Println("Start tally")
	var all_factors_submitted bool

	// check if factors are submitted
	all_factors_submitted, _ = check_factors(stub)

	var factor_buffer bytes.Buffer
	fmt.Println(all_factors_submitted)
	if all_factors_submitted == true {
		factor_buffer = get_all_factors(stub)

	}
	// election
	var v interface{}
	electionbyteValue, _ := stub.GetState("election")
	json.Unmarshal(electionbyteValue, &v)
	electionJSON, _ := json.MarshalIndent(v, "", " ")

	_ = ioutil.WriteFile("/helios/election.json", electionJSON, 0644)
	cmd := exec.Command("python", "/helios/helios/tally.py", "/helios/")
	fmt.Println("cmd line output", cmd.Args)
	out, err := cmd.CombinedOutput()
	if err != nil {
		fmt.Println(err)
	}
	fmt.Println(string(out))
	jsonFile, err := os.Open("result.json")
	if err != nil {
		fmt.Println(err)
	}
	defer jsonFile.Close()
	resultbyteValue, _ := ioutil.ReadAll(jsonFile)

	fmt.Println(string(resultbyteValue))
	stub.PutState("result", resultbyteValue)
	stub.PutState("factors", factor_buffer.Bytes())
	stub.SetEvent("invoked", factor_buffer.Bytes())
	return string(resultbyteValue), nil
}

func get_result(stub shim.ChaincodeStubInterface) (string, error) {
	resultbyteValue, _ := stub.GetState("result")
	factorsbyteValue, _ := stub.GetState("factors")
	var buffer bytes.Buffer
	buffer.Write([]byte(`{`))
	buffer.Write(resultbyteValue)
	buffer.Write([]byte(","))
	buffer.Write(factorsbyteValue)
	buffer.Write([]byte(`}`))
	return buffer.String(), nil
}

func set(stub shim.ChaincodeStubInterface, args []string) (string, error) {
	if len(args) != 2 {
		return "", fmt.Errorf("Incorrect arguments. Expecting a key and a value")
	}

	err := stub.PutState(args[0], []byte(args[1]))
	if err != nil {
		return "", fmt.Errorf("Failed to set asset: %s", args[0])
	}
	return args[1], nil
}

func get(stub shim.ChaincodeStubInterface, args []string) (string, error) {
	value, _ := stub.GetState(args[0])
	return string(value), nil
}

func main() {
	if err := shim.Start(new(heliosElection)); err != nil {
		fmt.Printf("Error starting heliosElection chaincode: %s", err)
	}
}
