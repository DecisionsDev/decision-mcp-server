import sys
import os

# Add the root directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

import pytest
from validator_collection import checkers
from decision_mcp_server.Credentials import Credentials  # Replace 'your_module' with the actual module name

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
    

def test_get_auth_bearer_token():
    # Test get_auth with bearer_token
    cred = Credentials(odm_url="http://localhost:9060/res", bearer_token="test_token")
    headers = cred.get_auth()
    assert headers == {
        'Authorization': 'Bearer test_token',
        'Content-Type': 'application/json; charset=UTF-8',
        'accept': 'application/json; charset=UTF-8'
    }

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