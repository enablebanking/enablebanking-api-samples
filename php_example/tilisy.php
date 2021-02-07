<?php

include 'vendor/autoload.php';

use \Firebase\JWT\JWT;

function request($url, $headers=[], $post='')
{
    $ch = curl_init();
    curl_setopt($ch, CURLOPT_URL, $url);
    curl_setopt($ch, CURLOPT_FOLLOWLOCATION, 1);
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
    curl_setopt($ch, CURLOPT_HEADER, 0);
    if(!empty($post))
    {
        curl_setopt($ch, CURLOPT_POSTFIELDS, $post);
    }
    if(count($headers))
    {
        curl_setopt($ch, CURLOPT_HTTPHEADER, $headers);
    }

    return ['body' => curl_exec($ch), 'status' => curl_getinfo($ch, CURLINFO_HTTP_CODE)];
}

// Reading and parsing config file
$config_file = file_get_contents(dirname(__FILE__) . '/../config.json');
$config = json_decode($config_file);

// Loading RSA private key
$key_path = $config->keyPath;
$rsa_key = file_get_contents($key_path);

// Creating JWT
$jwt_header = [ 'typ' => 'JWT', 'alg' => 'RS256', 'kid' => $config->applicationId ];
$payload = [
    'iss' => 'enablebanking.com',
    'aud' => 'api.tilisy.com',
    'iat' => time(),
    'exp' => time() + 3600
];
$jwt = JWT::encode($payload, $rsa_key, 'RS256', $config->applicationId);

$jwt = [
    'Authorization: Bearer ' . $jwt,
];

// Requesting application details
$r = request('https://api.tilisy.com/application', $jwt);
if($r['status'] === 200)
{
    $app = json_decode($r['body']);
    echo 'Application details:';
    print_r($app);
} else {
    echo 'Error response #' . $r['status'] . ':' . $r['body'];
}

// Requesting available ASPSPs
$r = request('https://api.tilisy.com/aspsps', $jwt);
if($r['status'] === 200)
{
    $aspsps = json_decode($r['body']);
    echo 'Available ASPSPs:';
    print_r($aspsps);
} else {
    echo 'Error response #' . $r['status'] . ':' . $r['body'];
}

// Starting authorization
$valid_until = time() + 2 * 7 * 24 * 60 * 60;
$body = [
    'access' => [ 'valid_until' => $valid_until ],
    'aspsp' => [ 'name' => 'Nordea', 'country' => 'FI' ], // { name: aspsps[0]['name'], country: aspsps[0]['country'] },
    'state' => 'random',
    'redirect_url' => $app->redirect_urls[0]
];

$r = request('https://api.tilisy.com/auth', $jwt, json_encode($body));
if($r['status'] == 200)
{
    $auth_url = json_decode($r['body'])->url;
    echo 'To authenticate open URL ' . $auth_url . PHP_EOL;
} else {
    echo 'Error response #' . $r['status'] . ':' . $r['body'];
}

// Reading auth code and creating user session
$auth_code = readline('Enter value of code parameter from the URL you were redirected to: ');

$body = json_encode([ 'code' => $auth_code ]);
$r = request('https://api.tilisy.com/sessions', $jwt, $body);
if($r['status'] === 200)
{
    $session = json_decode($r['body']);
    echo 'New user session has been created:';
    print_r($session); 
} else {
    echo 'Error response #' . $r['status'] . ':' . $r['body'];
}
$account_uid = $session->accounts[0]->uid;

// Retrieving account balances
$r = request('https://api.tilisy.com/accounts/' . $account_uid . '/balances', $jwt);
if($r['status'] === 200)
{
    $balances = json_decode($r['body'])->balances;
    echo 'Balances: ';
    print_r($balances);
} else {
    echo 'Error response #' . $r['status'] . ':' . $r['body'];
}

// Retrieving account transactions (since yesterday)
$continuation_key = null;
do
{
    $params = '?date_from=' . date('Y-m-d', strtotime('-1 day', time()));
    if($continuation_key)
    {
        $params .= '&continuation_key=' . $continuation_key;
    }
    $r = request('https://api.tilisy.com/accounts/' . $account_uid . '/transactions' . $params, $jwt);
    if($r['status'] === 200)
    {
        $rest_data = json_decode($r['body']);
        $transactions = $rest_data->transactions;
        echo 'Transactions:';
        print_r($transactions);
        if(isset($rest_data->continuation_key) && $rest_data->continuation_key)
        {
            $continuation_key = $rest_data->continuation_key;
            echo 'Going to fetch more transaction with continaution key ' . $continuation_key;
        } else {
            echo 'No continuation key. All transactions were fetched' . PHP_EOL;
            break;
        }
    } else {
        echo 'Error response #' . $r['status'] . ':' . $r['body'];
        break;
    }
}
while(true);