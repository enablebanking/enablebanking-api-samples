const fs = require("fs");
const jwa = require("jwa");
const readline = require('readline');


const base64AddPadding = (str) => {
  return str + "=".repeat((4 - str.length % 4) % 4);
}

const urlunsafeSignature = (signature) => {
  return signature.replace(/\_/g, "/").replace(/\-/g, "+");
}

const getJWTHeader = (applicationId) => {
  return encodeData({
    typ: "JWT",
    alg: "RS256",
    kid: applicationId
  })
}

const encodeData = (data) => {
  return Buffer.from(JSON.stringify(data)).toString("base64").replace("=", "")
}

const getJWTBody = (exp) => {
  const timestamp = Math.floor((new Date()).getTime() / 1000)
  return encodeData({
    iss: "enablebanking.com",
    aud: "api.tilisy.com",
    iat: timestamp,
    exp: timestamp + exp,
  })
}

const signWithKey = (data, keyPath) => {
  const key = fs.readFileSync(keyPath, "utf8");
  const hmac = jwa("RS256");
  return hmac.sign(data, key);
}

const getJWT = (applicationId, keyPath, exp = 3600) => {
  const jwtHeaders = getJWTHeader(applicationId)
  const jwtBody = getJWTBody(exp);
  const jwtSignature = signWithKey(`${jwtHeaders}.${jwtBody}`, keyPath)
  return `${jwtHeaders}.${jwtBody}.${jwtSignature}`
}

function input(query) {
  const rl = readline.createInterface({
      input: process.stdin,
      output: process.stdout,
  });

  return new Promise(resolve => rl.question(query, ans => {
      rl.close();
      resolve(ans);
  }))
}

function getCode(url) {
  const query = url.split("?")[1];
  for (const pair of query.split("&")) {
    const [key, val] = pair.split("=")
    if (key === "code") {
      return val;
    }
  }
}

module.exports = {
  getJWT: getJWT,
  input: input,
  getCode: getCode
}
