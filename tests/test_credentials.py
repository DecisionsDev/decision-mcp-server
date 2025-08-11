import sys
import os

# Add the root directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

import pytest
import responses
import json
import requests  # Add this line to import the requests module
from decision_mcp_server.Credentials import Credentials

def get_test_credentials():
    return Credentials(
        odm_url="http://localhost:9060/res",
        username="test_user",
        password="test_pass"
    )

def test_valid_url():
    # Test with a valid URL
    cred = Credentials(odm_url="http://localhost:9060/res")
    assert cred.odm_url == "http://localhost:9060/res"

def test_url_with_trailing_slash():
    # Test with a URL that has a trailing slash
    cred = Credentials(odm_url="http://localhost:9060/res/", username="user", password="pass")
    print(cred.odm_url)
    assert cred.odm_url == "http://localhost:9060/res"

def test_url_with_extra_path():
    # Test with a URL that has an extra path
    cred = Credentials(odm_url="http://localhost:9060/odm/res/", username="user", password="pass")
    assert cred.odm_url == "http://localhost:9060/odm/res"

def test_invalid_url():
    # Test with an invalid URL
    with pytest.raises(ValueError, match="'http://localh ost:9060/res' is not a valid URL"):
        Credentials(odm_url="http://localh ost:9060/res/", username="user", password="pass")

def test_get_auth_zenapikey():
    # Test get_auth with zenapikey
    cred = Credentials(odm_url="http://localhost:9060/res", username="test_username", zenapikey="test_key")
    headers = cred.get_auth()
    assert headers == {
        'Authorization': 'ZenApiKey dGVzdF91c2VybmFtZTp0ZXN0X2tleQ==', # Base64 encoded 'test_username:test_key'
        'Content-Type': 'application/json; charset=UTF-8',
        'accept': 'application/json; charset=UTF-8'
    }

def test_get_auth_missusername_zenapikey():
    # Test get_auth with zenapikey
     with pytest.raises(ValueError, match="Username must be provided when using zenapikey."):
        cred = Credentials(odm_url="http://localhost:9060/res", zenapikey="test_key", username=None)
        cred.get_auth()
    

def test_get_auth_basic_auth():
    # Test get_auth with username and password
    cred = Credentials(odm_url="http://localhost:9060/res", username="user", password="pass")
    headers = cred.get_auth()
    assert headers == {
        'Authorization': 'Basic dXNlcjpwYXNz',
        'Content-Type': 'application/json; charset=UTF-8',
        'accept': 'application/json; charset=UTF-8'
    }

def test_get_auth_no_credentials():
    # Test get_auth with no credentials
    cred = Credentials(odm_url="http://localhost:9060/res")
    with pytest.raises(ValueError, match="Either username and password, bearer token, or zenapikey must be provided."):
        cred.get_auth()

@responses.activate
def test_get_auth_openid_flow():
    """Test the complete OpenID Connect authentication flow with a mocked token endpoint."""
    
    # Mock token URL
    token_url = "https://auth.example.com/token"
    
    # Expected access token that will be returned by the mock server
    expected_token = "mocked_access_token_12345"
    
    # Set up the mock response for the token endpoint
    responses.add(
        responses.POST,
        token_url,
        json={
            "access_token": expected_token,
            "token_type": "Bearer",
            "expires_in": 3600,
            "scope": "openid"
        },
        status=200
    )
    
    # Create credentials with OpenID Connect parameters
    cred = Credentials(
        odm_url="http://localhost:9060/res",
        client_id="test_client_id",
        client_secret="test_client_secret",
        token_url=token_url,
        scope="openid profile"  # Test with multiple scopes
    )
    
    # Call get_auth which should make the token request
    headers = cred.get_auth()
    
    # Verify the token request was made correctly
    assert len(responses.calls) == 1
    assert responses.calls[0].request.url == token_url
    
    # Verify the request body contains the correct parameters
    request_body = responses.calls[0].request.body
    # Check if body is bytes, if so decode it, otherwise use as is
    if isinstance(request_body, bytes):
        request_body = request_body.decode('utf-8')
    
    assert "grant_type=client_credentials" in request_body
    assert "scope=openid+profile" in request_body
    
    # Verify the auth header uses HTTP Basic auth with client_id and client_secret
    auth_header = responses.calls[0].request.headers['Authorization']
    assert auth_header.startswith('Basic ')
    
    # Verify the returned headers contain the expected token
    assert headers == {
        'Authorization': f'Bearer {expected_token}',
        'Content-Type': 'application/json; charset=UTF-8',
        'accept': 'application/json; charset=UTF-8'
    }

@responses.activate
def test_get_auth_openid_error_handling():
    """Test error handling in the OpenID Connect authentication flow."""
    
    # Mock token URL
    token_url = "https://auth.example.com/token"
    
    # Set up the mock response to simulate a server error
    responses.add(
        responses.POST,
        token_url,
        json={
            "error": "invalid_client",
            "error_description": "Client authentication failed"
        },
        status=401
    )
    
    # Create credentials with OpenID Connect parameters
    cred = Credentials(
        odm_url="http://localhost:9060/res",
        client_id="invalid_client_id",
        client_secret="invalid_client_secret",
        token_url=token_url
    )
    
    # Call get_auth which should make the token request and raise an exception
    with pytest.raises(requests.exceptions.HTTPError) as excinfo:
        cred.get_auth()
    
    # Verify the correct error was raised
    assert "401" in str(excinfo.value)
    
    # Verify the token request was made
    assert len(responses.calls) == 1
    assert responses.calls[0].request.url == token_url

@responses.activate
def test_get_auth_openid_malformed_response():
    """Test handling of malformed responses in the OpenID Connect flow."""
    
    # Mock token URL
    token_url = "https://auth.example.com/token"
    
    # Set up the mock response with a malformed JSON body
    responses.add(
        responses.POST,
        token_url,
        body="Not a JSON response",
        status=200
    )
    
    # Create credentials with OpenID Connect parameters
    cred = Credentials(
        odm_url="http://localhost:9060/res",
        client_id="test_client_id",
        client_secret="test_client_secret",
        token_url=token_url
    )
    
    # Call get_auth which should make the token request and raise a JSON decoding exception
    with pytest.raises(json.JSONDecodeError):
        cred.get_auth()
    
    # Verify the token request was made
    assert len(responses.calls) == 1

@responses.activate
def test_get_auth_openid_missing_access_token():
    """Test handling when the token response is missing the access_token field."""
    
    # Mock token URL
    token_url = "https://auth.example.com/token"
    
    # Set up the mock response with a JSON body missing the access_token
    responses.add(
        responses.POST,
        token_url,
        json={
            "token_type": "Bearer",
            "expires_in": 3600
            # access_token is missing
        },
        status=200
    )
    
    # Create credentials with OpenID Connect parameters
    cred = Credentials(
        odm_url="http://localhost:9060/res",
        client_id="test_client_id",
        client_secret="test_client_secret",
        token_url=token_url
    )
    
    # Call get_auth which should make the token request and raise a KeyError
    with pytest.raises(KeyError) as excinfo:
        cred.get_auth()
    
    # Verify the correct error was raised
    assert "access_token" in str(excinfo.value)
    
    # Verify the token request was made
    assert len(responses.calls) == 1