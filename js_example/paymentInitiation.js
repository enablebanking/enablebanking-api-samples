'use strict';

const fetch = require('node-fetch');
const { getJWT, config } = require("./utils")


const main = async function () {
  const JWT = getJWT()
  const BASE_URL = "https://api.enablebanking.com"
  const REDIRECT_URL = config.redirectUrl
  const ASPSP_NAME = "S-Pankki"
  const ASPSP_COUNTRY = "FI"
  const baseHeaders = {
    Authorization: `Bearer ${JWT}`,
    "Content-Type": "application/json"
  }
  const applicationResponse = await fetch(`${BASE_URL}/application`, {
    headers: baseHeaders
  })
  console.log(`Application data: ${await applicationResponse.text()}`)

  const aspspsResponse = await fetch(`${BASE_URL}/aspsps`, {
    headers: baseHeaders
  })
  console.log(`ASPSPS data: ${await aspspsResponse.text()}`)

  // Initiating payment
  const body = {
    "payment_type": "SEPA",
    "payment_request": {
      "credit_transfer_transaction": [
        {
          "beneficiary": {
            "creditor_account": {
              "scheme_name": "IBAN",
              "identification": "FI7473834510057469",
            },
            "creditor": {
              "name": "Test",
            },
          },
          "instructed_amount": { "amount": "2.00", "currency": "EUR" },
          "reference_number": "123",
        }
      ],
    },
    "aspsp": { "name": ASPSP_NAME, "country": ASPSP_COUNTRY },
    "state": "some_test_state",
    "redirect_url": REDIRECT_URL,
    "psu_type": "personal",
  }
  const paymentResponse = await fetch(`${BASE_URL}/payments`, {
    method: "POST",
    headers: baseHeaders,
    body: JSON.stringify(body)
  })
  const paymentData = await paymentResponse.text();
  console.log(`Payment data: ${paymentData}`)
  const paymentDataJson = JSON.parse(paymentData)

  console.log("Use following credentials to authenticate: customera / 12345678")
  console.log("To authenticate open URL:")
  console.log(paymentDataJson.url)

  // Getting payment status
  // This request can be called multiple times to check the status of the payment
  const paymentId = paymentDataJson.payment_id
  const paymentStatusResponse = await fetch(`${BASE_URL}/payments/${paymentId}`, {
    headers: baseHeaders
  })
  const paymentStatusData = await paymentStatusResponse.text()
  console.log(`Payment status data: ${paymentStatusData}`)
};

(async () => {
  try {
    await main()
  } catch (error) {
    console.log(`Unexpected error happened: ${error}`)
  }
})();
