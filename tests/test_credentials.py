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
    
    # Ensure request_body is not None before assertions
    assert request_body is not None
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
def test_get_auth_pwjwt_with_public_cert():
    """Test PWJWT authentication with a public certificate for x5t computation."""
    import tempfile
    import os
    import base64
    import hashlib
    import jwt  # Make sure PyJWT is installed
    from unittest.mock import patch
    
    # Create temporary certificate files for testing
    with tempfile.NamedTemporaryFile(delete=False, suffix='.key') as private_key_file:
        # This is a test private key (not secure, just for testing)
        private_key = """-----BEGIN RSA PRIVATE KEY-----
MIIEpAIBAAKCAQEAu1SU1LfVLPHCozMxH2Mo4lgOEePzNm0tRgeLezV6ffAt0gun
VTLw7onLRnrq0/IzW7yWR7QkrmBL7jTKEn5u+qKhbwKfBstIs+bMY2Zkp18gnTxK
LxoS2tFczGkPLPgizskuemMghRniWWoLnB0/QILJvmjVWSv9ddnx6mT2J5Cv5KMD
Hq7Vdi3PzwJC2/Lw9VW1VVBswxWxIexPAlKe8LFzgawqiGWEUGXAGFy+I0IH8oes
C3T+fCmpgsTWMjCfBpvEIRaqFLy0EzDcg8FsThmZRY15RJJg+cAiAPgvEEB44zaJ
w+SkayLjej4qPfD2cQIDAQABAoIBAQDlJ+ScFfDgfDAbvYwFPGBGEYUYAGHb4bGd
EJXMiRawFRqTb1l5jCRjgEDVG3caeRlW/S7mE0IgkDWUwUCSjvwGXxrOzXCswA73
/HEu6Br9aWKGJu8EFP4QhSVYVZRIPocWSO5lbL8QlFUgEMTi5Srzu2WWQnRlSIFi
KxvSfs/EtQIBAQDRcQdz+1sT5g7iulAxqmz/OS7Qb0GTd0UE2xrV56cT+IlXAF3h
M+/VDzKk3DyDAAdlkXWtInOx1TetF2qpdb+zY8GRS8FkCKScc7gVP9z66cFlU82a
KvAybcWww2BWXL+al8VM/sE+W9JIdkrBuyVfMRfTU1s1OaBszKv+71EDdwIBAQBl
JDyr8WZCEfFmeadrh7t2kEjMzE/fjy3lF8oMrl9XrT+rxDGBnuSUx8BCJRcZUXLr
10RMtBWQo3G+zsB/D8mXw9m1Cv93G2P+ZFlpY9fQoIlxjsGtDCosSTm8VKNG8/V0
aXuIr8PYf6HgnH+DjMpHXEKLWdeqsRuKoYo3ZbEyFQIBAQDGAlR8ndMpcUcUEMSz
udr0mTsv50daJRri54jesvbDO6caLcLWIT1Tmy1FRRQvywdjeUPE0VdO4Ym1bGZM
aBhUsErwlm7QwkUHBW0xBOcbwVrj5qo0N1DTXYKxhBx/VGfmznBGb71FBTRX0czZ
gUcH45OnFljBB8PtQ+T/RZenIwIBAQCgwC/KJbEPKyDxV8GWcX7zOi+W5q9qXMJm
Y0mNaZHuYNJOdOKW9hCmUQY/BXBdd2KYkpRD0SnGfF/VQrZRfcXmLCExNYpMRTDN
2wZX7sXNh6AYwFdJKW8yP9FxoLUbNDmmYyPlqIiAcBKJvvwndZczROLmwLFgYUzw
qYQV1B0ATz0Yd6X+RGQhD6kocCRXJFmHhYjMdLINd+KKjOxSG0j3OKjzHEPLMpbp
QCQJVp0YqLKYXUYAA4VZi+MBpZA5KgZVIFQLm5IzQvuGqEQOMmCQC+Z2TPt8VQQN
t+Z1H5t2K+MG8ky6bo3QaSNBXOPHVnK/TQ0S171JfQDmzXJSPVEr
-----END RSA PRIVATE KEY-----"""
        private_key_file.write(private_key.encode())
        private_key_path = private_key_file.name
    
    with tempfile.NamedTemporaryFile(delete=False, suffix='.crt') as public_cert_file:
        # This is a test public certificate (not secure, just for testing)
        public_cert = """-----BEGIN CERTIFICATE-----
MIIDazCCAlOgAwIBAgIUOd70QQlNOIUgFoNNa7QzbdtKWucwDQYJKoZIhvcNAQEL
BQAwRTELMAkGA1UEBhMCQVUxEzARBgNVBAgMClNvbWUtU3RhdGUxITAfBgNVBAoM
GEludGVybmV0IFdpZGdpdHMgUHR5IEx0ZDAeFw0yMzA0MTIxNDQ2NDNaFw0yNDA0
MTExNDQ2NDNaMEUxCzAJBgNVBAYTAkFVMRMwEQYDVQQIDApTb21lLVN0YXRlMSEw
HwYDVQQKDBhJbnRlcm5ldCBXaWRnaXRzIFB0eSBMdGQwggEiMA0GCSqGSIb3DQEB
AQUAA4IBDwAwggEKAoIBAQC7VJTUt9Us8cKjMzEfYyjiWA4R4/M2bS1GB4t7NXp9
8C3SC6dVMvDuictGeurT8jNbvJZHtCSuYEvuNMoSfm76oqFvAp8Gy0iz5sxjZmSn
XyCdPEovGhLa0VzMaQ8s+CLOyS56YyCFGeJZagucHT9Agsm+aNVZK/112fHqZPYn
kK/kowMertV2Lc/PAkLb8vD1VbVVUGzDFbEh7E8CUp7wsXOBrCqIZYRQZcAYXL4j
Qgfyh6wLdP58KamCxNYyMJ8Gm8QhFqoUvLQTMNyDwWxOGZlFjXlEkmD5wCIA+C8Q
QHjjNonD5KRrIuN6Pio98PZxAgMBAAGjUzBRMB0GA1UdDgQWBBQNRxQMcVIlWiL7
RjXiqqFKmNKBQDAfBgNVHSMEGDAWgBQNRxQMcVIlWiL7RjXiqqFKmNKBQDAPBgNV
HRMBAf8EBTADAQH/MA0GCSqGSIb3DQEBCwUAA4IBAQCgwC/KJbEPKyDxV8GWcX7z
Oi+W5q9qXMJmY0mNaZHuYNJOdOKW9hCmUQY/BXBdd2KYkpRD0SnGfF/VQrZRfcXm
LCExNYpMRTDN2wZX7sXNh6AYwFdJKW8yP9FxoLUbNDmmYyPlqIiAcBKJvvwndZcz
ROLmwLFgYUzwqYQV1B0ATz0Yd6X+RGQhD6kocCRXJFmHhYjMdLINd+KKjOxSG0j3
OKjzHEPLMpbpQCQJVp0YqLKYXUYAA4VZi+MBpZA5KgZVIFQLm5IzQvuGqEQOMmCQ
C+Z2TPt8VQQNt+Z1H5t2K+MG8ky6bo3QaSNBXOPHVnK/TQ0S171JfQDmzXJSPVEr
-----END CERTIFICATE-----"""
        public_cert_file.write(public_cert.encode())
        public_cert_path = public_cert_file.name
    
    try:
        # Calculate the expected x5t value from the public certificate
        with open(public_cert_path, 'rb') as cert_file:
            cert_data = cert_file.read()
        
        # Calculate SHA-1 thumbprint
        sha1_hash = hashlib.sha1(cert_data).digest()
        expected_x5t = base64.urlsafe_b64encode(sha1_hash).rstrip(b'=').decode('utf-8')
        
        # Mock the jwt.encode function to avoid actual key parsing
        with patch('jwt.encode') as mock_encode:
            # Set up the mock to return a dummy JWT token
            mock_encode.return_value = "dummy.jwt.token"
            
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
            
            # Create credentials with PWJWT parameters
            cred = Credentials(
                odm_url="http://localhost:9060/res",
                client_id="test_client_id",
                jwt_cert_path=private_key_path,
                jwt_public_cert_path=public_cert_path,
                token_url=token_url
            )
            
            # Call get_auth which should make the token request
            headers = cred.get_auth()
            
            # Verify that jwt.encode was called with the correct headers
            # Get the headers argument from the call
            args, kwargs = mock_encode.call_args
            assert 'headers' in kwargs
            assert 'x5t' in kwargs['headers']
            assert kwargs['headers']['x5t'] == expected_x5t
            
            # Verify the token request was made
            assert len(responses.calls) == 1
            assert responses.calls[0].request.url == token_url
            
            # Verify the returned headers contain the expected token
            assert headers == {
                'Authorization': f'Bearer {expected_token}',
                'Content-Type': 'application/json; charset=UTF-8',
                'accept': 'application/json; charset=UTF-8'
            }
            
            # Test that providing only one of the certificate paths raises an error
            with pytest.raises(ValueError, match="Both 'jwt_cert_path' and 'jwt_public_cert_path' are required for PWJWT authentication."):
                Credentials(
                    odm_url="http://localhost:9060/res",
                    client_id="test_client_id",
                    jwt_cert_path=private_key_path,  # Only providing private key
                    token_url=token_url
                ).get_auth()
                
            with pytest.raises(ValueError, match="Both 'jwt_cert_path' and 'jwt_public_cert_path' are required for PWJWT authentication."):
                Credentials(
                    odm_url="http://localhost:9060/res",
                    client_id="test_client_id",
                    jwt_public_cert_path=public_cert_path,  # Only providing public cert
                    token_url=token_url
                ).get_auth()
    
    finally:
        # Clean up temporary files
        if os.path.exists(private_key_path):
            os.unlink(private_key_path)
        if os.path.exists(public_cert_path):
            os.unlink(public_cert_path)

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