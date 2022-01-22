package main

type Access struct {
	ValidUntil string `json:"valid_until"`
}

type Aspsp struct {
	Name    string `json:"name"`
	Country string `json:"country"`
}

type AuthorizationBody struct {
	Access      Access `json:"access"`
	Aspsp       Aspsp  `json:"aspsp"`
	State       string `json:"state"`
	RedirectUrl string `json:"redirect_url"`
	PsuType     string `json:"psu_type"`
}

// Only used fields are added
type AuthorizeSessionBody struct {
	Code string `json:"code"`
}

type Account struct {
	Uid string `json:"uid"`
}

type AuthorizedSession struct {
	SessionId string `json:"session_id"`
	Accounts  []Account
}
