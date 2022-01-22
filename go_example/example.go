package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"github.com/google/uuid"
	"io/ioutil"
	"net/http"
	"net/url"
	"time"
)

const keyPath = "/path/to/key.pem"
const appId = "your-app-id"
const APIOrigin = "https://api.tilisy.com"
const ASPSPName = "Nordea"
const ASPSPCountry = "FI"

func main() {
	jwt, err := getJwt(keyPath, appId)
	if err != nil {
		panic(err)
	}

	client := &http.Client{}
	request, err := http.NewRequest("GET", APIOrigin+"/application", nil)
	if err != nil {
		panic(err)
	}
	request.Header.Add("Authorization", "Bearer "+jwt)
	response, err := client.Do(request)
	if err != nil {
		panic(err)
	}
	defer response.Body.Close()
	body, err := ioutil.ReadAll(response.Body)
	if err != nil {
		panic(err)
	}
	fmt.Print("Application details: ")
	fmt.Println(string(body))

	request, err = http.NewRequest("GET", APIOrigin+"/aspsps", nil)
	if err != nil {
		panic(err)
	}
	request.Header.Add("Authorization", "Bearer "+jwt)
	response, err = client.Do(request)
	if err != nil {
		panic(err)
	}
	defer response.Body.Close()
	body, err = ioutil.ReadAll(response.Body)
	if err != nil {
		panic(err)
	}
	// Commented out, because output is too long
	//fmt.Print("ASPSP list: ")
	//fmt.Println(string(body))

	// Starting authorization
	validUntil := (time.Now().AddDate(0, 0, 1)).Format(time.RFC3339)
	startAuthRequestBody := AuthorizationBody{
		Access: Access{
			ValidUntil: validUntil,
		},
		Aspsp: Aspsp{
			Name:    ASPSPName,
			Country: ASPSPCountry,
		},
		State:       uuid.NewString(),
		RedirectUrl: "https://enablebanking.com/auth_redirect",
		PsuType:     "personal",
	}
	jsonRequestBody, err := json.Marshal(startAuthRequestBody)
	if err != nil {
		panic(err)
	}
	request, err = http.NewRequest("POST", APIOrigin+"/auth", bytes.NewBuffer(jsonRequestBody))
	if err != nil {
		panic(err)
	}
	request.Header.Add("Authorization", "Bearer "+jwt)
	request.Header.Add("Content-Type", "application/json")
	response, err = client.Do(request)
	if err != nil {
		panic(err)
	}
	defer response.Body.Close()
	body, err = ioutil.ReadAll(response.Body)
	if err != nil {
		panic(err)
	}
	fmt.Print("To authenticate open URL: ")
	responseJson := struct {
		Url string `json:"url"`
	}{}
	err = json.Unmarshal(body, &responseJson)
	if err != nil {
		panic(err)
	}
	fmt.Println(responseJson.Url)

	fmt.Println("Paste here the URL you have been redirected to: ")
	var redirectUrlString string
	fmt.Scanln(&redirectUrlString)
	redirectUrl, err := url.Parse(redirectUrlString)
	if err != nil {
		panic(err)
	}
	authorizationCode := redirectUrl.Query().Get("code")
	authorizeSessionRequestBody := AuthorizeSessionBody{
		Code: authorizationCode,
	}
	jsonRequestBody, err = json.Marshal(authorizeSessionRequestBody)
	if err != nil {
		panic(err)
	}
	request, err = http.NewRequest("POST", APIOrigin+"/sessions", bytes.NewBuffer(jsonRequestBody))
	if err != nil {
		panic(err)
	}
	request.Header.Add("Authorization", "Bearer "+jwt)
	request.Header.Add("Content-Type", "application/json")
	response, err = client.Do(request)
	if err != nil {
		panic(err)
	}
	defer response.Body.Close()
	body, err = ioutil.ReadAll(response.Body)
	if err != nil {
		panic(err)
	}
	authorizeSessionResponse := AuthorizedSession{}
	err = json.Unmarshal(body, &authorizeSessionResponse)
	fmt.Printf("Session id: %s\n", authorizeSessionResponse.SessionId)
	accountId := authorizeSessionResponse.Accounts[0].Uid

	// Get account balances
	request, err = http.NewRequest("GET", APIOrigin+"/accounts/"+accountId+"/balances", nil)
	if err != nil {
		panic(err)
	}
	request.Header.Add("Authorization", "Bearer "+jwt)
	request.Header.Add("Content-Type", "application/json")
	response, err = client.Do(request)
	if err != nil {
		panic(err)
	}
	defer response.Body.Close()
	body, err = ioutil.ReadAll(response.Body)
	if err != nil {
		panic(err)
	}
	fmt.Print("Account balances: ")
	fmt.Println(string(body))

	// Get account transactions
	request, err = http.NewRequest("GET", APIOrigin+"/accounts/"+accountId+"/transactions", nil)
	if err != nil {
		panic(err)
	}
	request.Header.Add("Authorization", "Bearer "+jwt)
	request.Header.Add("Content-Type", "application/json")
	response, err = client.Do(request)
	if err != nil {
		panic(err)
	}
	defer response.Body.Close()
	body, err = ioutil.ReadAll(response.Body)
	if err != nil {
		panic(err)
	}
	fmt.Print("Account transactions: ")
	fmt.Println(string(body))
}
