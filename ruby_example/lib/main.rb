require 'bundler/setup'

require 'faraday'
require 'json'
require 'jwt'
require 'pp'
require 'time'

def main
  # Reading and parsing config file
  config_file = File.read("../config.json")
  config = JSON.parse(config_file)

  # Loading RSA private key
  key_path = "../" + config["keyPath"]
  rsa_key = OpenSSL::PKey::RSA.new(File.read(key_path))

  # Creating JWT
  iat = Time.now.to_i
  jwt_header = { typ: "JWT", alg: "RS256", kid: config["applicationId"] }
  jwt_body = { iss: "enablebanking.com", aud: "api.tilisy.com", iat: iat, exp: iat + 3600 } 
  jwt = JWT.encode(jwt_body, rsa_key, 'RS256', jwt_header)

  # Requesting application details
  r = Faraday.get("https://api.tilisy.com/application", nil, "Authorization" => "Bearer #{jwt}")
  if r.status == 200
    app = JSON.parse(r.body)
    puts "Application details:"
    puts pp(app)
  else
    puts "Error response #{r.status}:", r.body
    return
  end

  # Requesting available ASPSPs
  r = Faraday.get("https://api.tilisy.com/aspsps", nil, "Authorization" => "Bearer #{jwt}")
  if r.status == 200
    aspsps = JSON.parse(r.body)["aspsps"]
    puts "Available ASPSPs:"
    puts pp(aspsps)
  else
    puts "Error response #{r.status}:", r.body
    return
  end

  # Starting authorization"
  valid_until = Time.now + 2*7*24*60*60 # 2 weeks
  body = {
    access: { valid_until: valid_until.utc.iso8601 },
    aspsp: { name: "Nordea", country: "FI" }, # { name: aspsps[0]["name"], country: aspsps[0]["country"] },
    state: "random",
    redirect_url: app["redirect_urls"][0]
  }
  headers = {
    "Content-Type" => "application/json",
    "Authorization" => "Bearer #{jwt}"
  }
  r = Faraday.post("https://api.tilisy.com/auth", JSON.dump(body), headers)
  if r.status == 200
    auth_url = JSON.parse(r.body)["url"]
    puts "To authenticate open URL #{auth_url}"
  else
    puts "Error response #{r.status}:", r.body
    return
  end

  # Reading auth code and creating user session
  puts "Enter value of code parameter from the URL you were redirected to:"
  auth_code = nil
  ARGF.each_line do |line|
    auth_code = line.gsub(/\s/, "")
    break
  end
  body = { code: auth_code }
  r = Faraday.post("https://api.tilisy.com/sessions", JSON.dump(body), headers)
  if r.status == 200
    session = JSON.parse(r.body)
    puts "New user session has been created:"
    puts pp(session)
  else
    puts "Error response #{r.status}:", r.body
    return
  end

  if session["accounts"].length() == 0
    puts "No accounts available"
    return
  end

  # Retrieving account balances
  account_uid = session["accounts"][0]["uid"]
  r = Faraday.get(
    "https://api.tilisy.com/accounts/#{account_uid}/balances",
    nil,
    "Authorization" => "Bearer #{jwt}"
  )
  if r.status == 200
    balances = JSON.parse(r.body)["balances"]
    puts "Balances:"
    puts balances
  else
    puts "Error response #{r.status}:", r.body
    return
  end

  # Retrieving account transactions (since yesterday)
  continuation_key = nil
  loop do
    query = { date_from: Date.today.prev_day.iso8601 }
    if continuation_key
      query["continuation_key"] = continuation_key
    end
    r = Faraday.get(
      "https://api.tilisy.com/accounts/#{account_uid}/transactions",
      query,
      "Authorization" => "Bearer #{jwt}"
    )
    if r.status == 200
      resp_data = JSON.parse(r.body)
      transactions = resp_data["transactions"]
      puts "Transactions:"
      puts transactions
      if resp_data.has_key?("continuation_key") and resp_data["continuation_key"]
        continuation_key = resp_data["continuation_key"]
        puts "Going to fetch more transaction with continuation key #{continuation_key}"
      else
        puts "No continuation key. All transactions were fetched"
        break
      end
    else
      puts "Error response #{r.status}:", r.body
      return
    end
  end
  puts "All done!"
end

if __FILE__ == $PROGRAM_NAME
  main
end
