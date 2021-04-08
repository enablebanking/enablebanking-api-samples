using System;
using System.Collections.Generic;
using System.IO;
using System.IdentityModel.Tokens.Jwt;
using System.Net.Http;
using System.Net.Http.Headers;
using System.Security.Claims;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using System.Text.Json.Serialization;
using System.Threading.Tasks;
using System.Web;

using Microsoft.IdentityModel.Tokens;

namespace cs_example
{
    class Program
    {
        private static readonly HttpClient client = new HttpClient();
        private static readonly string apiOrigin = "https://api.tilisy.com";
        private static readonly string jwtAudience = "api.tilisy.com";
        private static readonly string jwtIssuer = "enablebanking.com";

        private static string authRedirectUrl = null;

        static string CreateToken(string keyPath, string appKid)
        {
            var privateKey = File.ReadAllText(keyPath);
            var privateKeyLines = privateKey.Split(new[] { Environment.NewLine }, StringSplitOptions.None);
            var privateKeyEncoded = "";
            for (int i = 1; i < privateKeyLines.Length - 2; i++) {
                privateKeyEncoded += privateKeyLines[i];
            }
            var privateKeyBytes = Convert.FromBase64String(privateKeyEncoded);
            using RSA rsa = RSA.Create();
            rsa.ImportRSAPrivateKey(privateKeyBytes, out _);

            var signingCredentials = new SigningCredentials(new RsaSecurityKey(rsa), SecurityAlgorithms.RsaSha256)
            {
                CryptoProviderFactory = new CryptoProviderFactory { CacheSignatureProviders = false }
            };

            var now = DateTime.Now;
            var unixTimeSeconds = new DateTimeOffset(now).ToUnixTimeSeconds();

            var jwt = new JwtSecurityToken(
                audience: jwtAudience,
                issuer: jwtIssuer,
                claims: new Claim[] {
                    new Claim(JwtRegisteredClaimNames.Iat, unixTimeSeconds.ToString(), ClaimValueTypes.Integer64)
                },
                expires: now.AddMinutes(30),
                signingCredentials: signingCredentials
            );
            jwt.Header.Add("kid", appKid);
            return new JwtSecurityTokenHandler().WriteToken(jwt);
        }

        static async Task Main(string[] args)
        {
            // Reading config
            Dictionary<string, string> config = JsonSerializer.Deserialize<Dictionary<string, string>>(
                File.ReadAllText("../config.json")
            );
            string keyPath = "../" + config["keyPath"];
            string appKid = config["applicationId"];

            // Creating JWT and setting to client
            string jwt = CreateToken(keyPath, appKid);
            Console.WriteLine("Created application JwT:");
            Console.WriteLine(jwt);
            client.DefaultRequestHeaders.Authorization = new AuthenticationHeaderValue("Bearer", jwt);

            // Requesting application details
            var r = await client.GetAsync(apiOrigin + "/application");
            if (r.IsSuccessStatusCode) {
                string json = await r.Content.ReadAsStringAsync();
                var app = JsonSerializer.Deserialize<Dictionary<string, JsonElement>>(json);
                Console.WriteLine($"App name: {app["name"]}");
                Console.WriteLine($"App description: {app["description"]}");
                Console.WriteLine($"App redirect URLs:");
                foreach (var redirectUrl in app["redirect_urls"].EnumerateArray())
                {
                    Console.WriteLine($"- {redirectUrl}");
                    // setting for later use
                    if (authRedirectUrl == null) {
                        authRedirectUrl = redirectUrl.ToString();
                    }
                }
            }
            else {
                Console.WriteLine($"Error response {r.StatusCode}:");
                Console.WriteLine(await r.Content.ReadAsStringAsync());
                return;
            }

            // Requesting available ASPSPs
            r = await client.GetAsync(apiOrigin + "/aspsps");
            if (r.IsSuccessStatusCode) {
                string json = await r.Content.ReadAsStringAsync();
                var data = JsonSerializer.Deserialize<Dictionary<string, JsonElement>>(json);
                Console.WriteLine("Available ASPSPs:");
                foreach (var aspsp in data["aspsps"].EnumerateArray())
                {
                    Console.WriteLine($"- {aspsp}");
                }
            }
            else {
                Console.WriteLine($"Error response {r.StatusCode}:");
                Console.WriteLine(await r.Content.ReadAsStringAsync());
                return;
            }

            // Starting authorization
            var body = new Dictionary<string, object>() {
                { "access", new Dictionary<string, string>() {
                    { "valid_until", DateTime.UtcNow.AddDays(10).ToString("u") }
                }},
                { "aspsp", new Dictionary<string, string>() {
                    { "name", "Nordea" },
                    { "country", "FI" }
                }},
                { "state", System.Guid.NewGuid().ToString() },
                { "redirect_url", authRedirectUrl },
                { "psu_type", "personal" }
            };
            Console.WriteLine();
            r = await client.PostAsync(apiOrigin + "/auth", new StringContent(JsonSerializer.Serialize(body), Encoding.UTF8, "application/json"));
            if (r.IsSuccessStatusCode) {
                string json = await r.Content.ReadAsStringAsync();
                var data = JsonSerializer.Deserialize<Dictionary<string, string>>(json);
                Console.WriteLine($"To authenticate open URL {data["url"]}");
            }
            else {
                Console.WriteLine($"Error response {r.StatusCode}:");
                Console.WriteLine(await r.Content.ReadAsStringAsync());
                return;
            }

            // Reading auth code and creating user session
            Console.Write("Paste here the URL you have been redirected to: ");
            var redirectedUrl = Console.ReadLine();
            var code = HttpUtility.ParseQueryString(new Uri(redirectedUrl).Query)["code"];
            body = new Dictionary<string, object>() {
                { "code", code }
            };
            r = await client.PostAsync(apiOrigin + "/sessions", new StringContent(JsonSerializer.Serialize(body), Encoding.UTF8, "application/json"));
            if (r.IsSuccessStatusCode) {
                string json = await r.Content.ReadAsStringAsync();
                var data = JsonSerializer.Deserialize<Dictionary<string, JsonElement>>(json);
                Console.WriteLine($"New user session {data["session_id"]} has been created. The following accounts are available:");
                foreach (var account in data["accounts"].EnumerateArray())
                {
                    Console.WriteLine($"- {account}");
                }
            }
            else {
                Console.WriteLine($"Error response {r.StatusCode}:");
                Console.WriteLine(await r.Content.ReadAsStringAsync());
                return;
            }
        }
    }
}
