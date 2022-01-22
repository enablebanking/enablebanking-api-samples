package main

import (
	"crypto"
	"crypto/rand"
	"crypto/rsa"
	"crypto/sha256"
	"crypto/x509"
	"encoding/base64"
	"encoding/json"
	"encoding/pem"
	"errors"
	"fmt"
	"io/ioutil"
	"time"
)

func readKey(path string) ([]byte, error) {
	file, err := ioutil.ReadFile(path)
	if err != nil {
		return nil, err
	}
	return file, nil
}

func loadPrivateKey(path string) (*rsa.PrivateKey, error) {
	keyContent, err := readKey(path)
	if err != nil {
		return nil, err
	}
	block, _ := pem.Decode(keyContent)
	if block == nil {
		return nil, errors.New("failed to parse PEM private key")
	}
	switch block.Type {
	case "RSA PRIVATE KEY":
		privateKey, err := x509.ParsePKCS1PrivateKey(block.Bytes)
		if err != nil {
			return nil, err
		}
		return privateKey, nil
	case "PRIVATE KEY":
		privateKey, err := x509.ParsePKCS8PrivateKey(block.Bytes)
		if err != nil {
			return nil, err
		}
		return privateKey.(*rsa.PrivateKey), nil
	default:
		fmt.Println("Unsupported key type:", block.Type)
		return nil, errors.New("failed to parse PEM private key")
	}
}

func sign(privateKey *rsa.PrivateKey, data []byte) (string, error) {
	hash := sha256.New()
	hash.Write(data)
	hashed := hash.Sum(nil)
	signature, err := rsa.SignPKCS1v15(rand.Reader, privateKey, crypto.SHA256, hashed)
	if err != nil {
		return "", err
	}
	encodedSignature := base64.RawURLEncoding.EncodeToString(signature)
	return encodedSignature, nil
}

func getJwtHeader(appId string) (string, error) {
	encodedHeader, err := json.Marshal(struct {
		Alg string `json:"alg"`
		Typ string `json:"typ"`
		Kid string `json:"kid"`
	}{
		Alg: "RS256",
		Typ: "JWT",
		Kid: appId,
	})
	if err != nil {
		return "", err
	}
	return base64.RawURLEncoding.EncodeToString(encodedHeader), nil
}

func getJwtBody() (string, error) {
	iat := time.Now().Unix()
	encodedBody, err := json.Marshal(struct {
		Iss string `json:"iss"`
		Aud string `json:"aud"`
		Iat int64  `json:"iat"`
		Exp int64  `json:"exp"`
	}{
		Iss: "enablebanking.com",
		Aud: "api.tilisy.com",
		Iat: iat,
		Exp: iat + 3600,
	})
	if err != nil {
		return "", err
	}
	return base64.RawURLEncoding.EncodeToString(encodedBody), nil
}

func getJwt(keyPath string, appId string) (string, error) {
	header, err := getJwtHeader(appId)
	if err != nil {
		return "", err
	}
	body, err := getJwtBody()
	if err != nil {
		return "", err
	}
	signBody := fmt.Sprintf("%s.%s", header, body)
	privateKey, err := loadPrivateKey(keyPath)
	if err != nil {
		return "", err
	}
	signature, err := sign(privateKey, []byte(signBody))
	if err != nil {
		return "", err
	}
	return fmt.Sprintf("%s.%s", signBody, signature), nil
}
