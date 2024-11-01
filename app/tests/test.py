"""
Unit tests for authentication routes in the Talent application.
"""
import requests

token ="eyJhbGciOiJSUzI1NiIsImtpZCI6ImU2YWMzNTcyNzY3ZGUyNjE0ZmM1MTA4NjMzMDg3YTQ5MjMzMDNkM2IiLCJ0eXAiOiJKV1QifQ.eyJpc3MiOiJodHRwczovL3NlY3VyZXRva2VuLmdvb2dsZS5jb20vdGFsZW50LWRkN2RkIiwiYXVkIjoidGFsZW50LWRkN2RkIiwiYXV0aF90aW1lIjoxNzMwMzg5MDA3LCJ1c2VyX2lkIjoiQlB1NUlkOVJ6N2RSVWFuRVp3S2RvZGVtZW5GMyIsInN1YiI6IkJQdTVJZDlSejdkUlVhbkVad0tkb2RlbWVuRjMiLCJpYXQiOjE3MzAzODkwMDcsImV4cCI6MTczMDM5MjYwNywiZW1haWwiOiJ0ZXN0MTIzQGdtYWlsLmNvbSIsImVtYWlsX3ZlcmlmaWVkIjpmYWxzZSwiZmlyZWJhc2UiOnsiaWRlbnRpdGllcyI6eyJlbWFpbCI6WyJ0ZXN0MTIzQGdtYWlsLmNvbSJdfSwic2lnbl9pbl9wcm92aWRlciI6InBhc3N3b3JkIn19.T5bt5prJTncrv4xezveoffoa3Cjvi8OAkmNbBc-k9wPvN3GUEWdeZDQXlwG_r0H6qNu_rCkNAD9UzNVxuuAs9XOzQ47ZYrgttRN633sfi91aJB0hf7GWq1pK0-e9Q4K7MVY7QJAE2RYEMcU3nItkfH2t1EEOWYW6fSD2ZH0JyrNU3-gAWHK7iIxIW-_JFTlVhbW3ExVgx_pOVzFBUDztLsaj-LsGnHOWiF30oXtyi_tlMs8iiHHiE4xvjDrcXxces8TjPFTtVZKIhMLDSJH1xOnlvfLCR7ONwAaSKf2tBYDWD-VxyP2MGoK12dau3NgJHP1WyjarZxVWih4mODzK1g"

def test_validate_endpoint():
    """
    Tests the authentication route for successful login.
    """
    headers = {
        "authorization": f"{token}"
    }
    response = requests.post(
        "http://127.0.0.1:8000/ping",
        headers=headers
    )

    return response.text

print(test_validate_endpoint())
