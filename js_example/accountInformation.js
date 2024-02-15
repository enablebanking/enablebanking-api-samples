'use strict';

const fetch = require('node-fetch');
const {getJWT, config, input, getCode} = require("./utils")


const main = async function() {
  const JWT = getJWT()
  const BASE_URL = "https://api.enablebanking.com"
  const REDIRECT_URL = config.redirectUrl
  const BANK_NAME = "Nordea"
  const BANK_COUNTRY = "FI"
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
  // If you want you can override BANK_NAME and BANK_COUNTRY with any bank from this list
  console.log(`ASPSPS data: ${await aspspsResponse.text()}`)

  // 10 days ahead
  const validUntil = new Date(new Date().getTime() + 10 * 24 * 60 * 60 * 1000);
  const startAuthorizationBody = {
    access: {
      valid_until: validUntil.toISOString()
    },
    aspsp: {
      name: BANK_NAME,
      country: BANK_COUNTRY
    },
    state: "some_test_state",
    redirect_url: REDIRECT_URL,
    psu_type: "personal"
  }
  const psuHeaders = {
    ...baseHeaders,
    "psu-ip-address": "10.10.10.10",
    "psu-user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:80.0) Gecko/20100101 Firefox/80.0"
  }
  const startAuthorizationResponse = await fetch(`${BASE_URL}/auth`, {
    method: "POST",
    headers: psuHeaders,
    body: JSON.stringify(startAuthorizationBody)
  })
  const startAuthorizationData = await startAuthorizationResponse.text();
  console.log(`Start authorization data: ${startAuthorizationData}`)
  const redirectedUrl = await input(`Please go to ${ JSON.parse(startAuthorizationData)["url"] }, authorize consent and paste here the url you have been redirected to: `)

  const createSessionBody = {
    code: getCode(redirectedUrl)
  }
  const createSessionResponse = await fetch(`${BASE_URL}/sessions`, {
    method: "POST",
    headers: psuHeaders,
    body: JSON.stringify(createSessionBody)
  })
  const createSessionData = await createSessionResponse.text()
  console.log(`Create session data: ${createSessionData}`)
  const sessionId = JSON.parse(createSessionData).session_id

  const sessionResponse = await fetch(`${BASE_URL}/sessions/${sessionId}`, {
    headers: baseHeaders
  })
  const sessionData = await sessionResponse.text()
  console.log(`Session data ${sessionData}`)

  const accountId = JSON.parse(sessionData).accounts[0]
  const accountBalancesResponse = await fetch(`${BASE_URL}/accounts/${accountId}/balances`, {
    headers: psuHeaders
  })
  console.log(`Account balances data: ${await accountBalancesResponse.text()}`)

  const accountTransactionsResponse = await fetch(`${BASE_URL}/accounts/${accountId}/transactions`, {
    headers: psuHeaders
  })
  console.log(`Account transactions data: ${await accountTransactionsResponse.text()}`)
};

(async () => {
  try{
    await main()
  } catch (error) {
    console.log(`Unexpected error happened: ${error}`)
  }
})();
