package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"github.com/google/uuid"
	"io"
	"io/ioutil"
	"net/http"
)

const configPath = "../config.json"
const APIOrigin = "https://api.enablebanking.com"
const ASPSPName = "S-Pankki"
const ASPSPCountry = "FI"

func main() {
	config := Config{}
	configFile, err := ioutil.ReadFile(configPath)
	err = json.Unmarshal(configFile, &config)
	if err != nil {
		panic(err)
	}
	jwt, err := getJwt(config.KeyPath, config.ApplicationId)
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

	// Initiating a payment
	paymentBody := map[string]interface{}{
		"payment_type": "SEPA",
		"payment_request": map[string]interface{}{
			"credit_transfer_transaction": []interface{}{
				map[string]interface{}{
					"beneficiary": map[string]interface{}{
						"creditor_account": map[string]string{
							"scheme_name":    "IBAN",
							"identification": "FI7473834510057469",
						},
						"creditor": map[string]interface{}{
							"name": "John Doe",
						},
					},
					"instructed_amount": map[string]string{
						"currency": "EUR",
						"amount":   "100.00",
					},
					"reference_number": "123",
				},
			},
		},
		"aspsp": map[string]string{
			"name":    ASPSPName,
			"country": ASPSPCountry,
		},
		"state":        uuid.NewString(),
		"redirect_url": config.RedirectUrl,
		"psu_type":     "personal",
	}
	paymentBodyJson, err := json.Marshal(paymentBody)
	if err != nil {
		panic(err)
	}
	request, err = http.NewRequest("POST", APIOrigin+"/payments", bytes.NewBuffer(paymentBodyJson))
	if err != nil {
		panic(err)
	}
	request.Header.Add("Authorization", "Bearer "+jwt)
	response, err = client.Do(request)
	if err != nil {
		panic(err)
	}
	defer func(Body io.ReadCloser) {
		err := Body.Close()
		if err != nil {
			panic(err)
		}
	}(response.Body)

	body, err = io.ReadAll(response.Body)
	if err != nil {
		panic(err)
	}
	responseJson := struct {
		Url       string `json:"url"`
		PaymentId string `json:"payment_id"`
	}{}
	err = json.Unmarshal(body, &responseJson)
	if err != nil {
		panic(err)
	}

	fmt.Println("Use following credentials to authenticate: customera / 12345678")
	fmt.Print("To authenticate open URL: ")
	fmt.Println(responseJson.Url)

	// This request can be called multiple times to check the status of the payment
	paymentStatusRequest, err := http.NewRequest("GET", APIOrigin+"/payments/"+responseJson.PaymentId, nil)
	if err != nil {
		panic(err)
	}
	paymentStatusRequest.Header.Add("Authorization", "Bearer "+jwt)
	paymentStatusResponse, err := client.Do(paymentStatusRequest)
	if err != nil {
		panic(err)
	}
	defer func(Body io.ReadCloser) {
		err := Body.Close()
		if err != nil {
			panic(err)
		}
	}(paymentStatusResponse.Body)
	paymentStatusBody, err := io.ReadAll(paymentStatusResponse.Body)
	if err != nil {
		panic(err)
	}
	fmt.Print("Payment status: ")
	fmt.Println(string(paymentStatusBody))
}
