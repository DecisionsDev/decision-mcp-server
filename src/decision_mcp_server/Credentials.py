import requests
from requests.adapters import HTTPAdapter
import ssl
from validator_collection import  checkers
import base64
import logging
import json

class CustomHTTPAdapter(HTTPAdapter):
    """
    A class that modifies the default behaviour with regards to certificates in order to
        - accept self-signed certificates
        - skip hostname verification
    """
    def __init__(self, certfile=None):
         self.certfile = certfile
         HTTPAdapter.__init__(self)
         
    def init_poolmanager(self, *args, **kwargs):
        context = ssl.create_default_context(cafile = self.certfile)
        context.verify_flags = ssl.VERIFY_ALLOW_PROXY_CERTS | ssl.VERIFY_X509_TRUSTED_FIRST | ssl.VERIFY_X509_PARTIAL_CHAIN
        kwargs['ssl_context'] = context
        kwargs['assert_hostname'] = False
        return super().init_poolmanager(*args, **kwargs)

class Credentials:
    """
    A class to handle credentials for accessing an ODM (Operational Decision Manager) service.

    Attributes:
    -----------
    odm_url : str
        The base URL for the ODM service.
    odm_url_runtime : str, optional
        The runtime URL for the ODM service. If not provided, it defaults to odm_url.
    username : str, optional
        The username for basic authentication.
    password : str, optional
        The password for basic authentication.
    token_url : str, optional
        The OpenID URL to retrieve an access token for OpenID authentication.
    scope : str, optional
        The value of the 'scope' parameter in the request sent to the OP to retrieve an access token for OpenID authentication using Client Credentials.
        The default value is 'openid'
    client_id : str, optional
        The OpenID Client Id to connect to the ODM product for OpenID authentication.
    client_secret : str, optional
        The OpenID Client Secret to connect to the ODM product for OpenID authentication.
    zenapikey : str, optional
        The ZenAPI key for API key-based authentication.
    verify_ssl : bool, optional
        Whether to verify SSL certificates. Defaults to True.
    ssl_cert_path : str, optional
        Path to the SSL certificate file. If not provided, defaults to system certificates.
    debug : bool, optional
        Whether to enable HTTP debug logging. Defaults to False.

    Methods:
    --------
    get_auth():
        Returns the appropriate authentication headers based on the provided credentials.
    get_session():
        Creates and returns a requests Session object configured with SSL settings.
    """
    def __init__(self, odm_url, odm_url_runtime=None, token_url=None, scope='openid', client_id=None, client_secret=None, username=None, password=None, zenapikey=None, verify_ssl=True, ssl_cert_path=None, debug=False):

        self.odm_url=odm_url.rstrip('/') 
        if odm_url_runtime is not None:
           logging.info("Using provided runtime URL: " + odm_url_runtime)
           self.odm_url_runtime=odm_url_runtime.rstrip('/')  
        else:
            self.odm_url_runtime=self.odm_url
                # Check if the URL ends with 'res' and replace it with 'DecisionService'
            if self.odm_url_runtime.endswith('res'):
                self.odm_url_runtime=self.odm_url_runtime[:-3] + 'DecisionService'
            logging.info("No runtime URL provided, using odm_url as root runtime URL."+self.odm_url_runtime)
        if not checkers.is_url(self.odm_url):
            raise ValueError("'"+self.odm_url+"' is not a valid URL")

        if verify_ssl:
            import certifi
            self.cacert = certifi.where()
        else:
            self.cacert = None

        self.username = username
        self.password = password
        self.token_url = token_url
        self.scope = scope
        self.client_id = client_id
        self.client_secret = client_secret
        self.zenapikey = zenapikey
        self.verify_ssl = verify_ssl
        self.ssl_cert_path = ssl_cert_path
        self.debug = debug

    def get_auth(self):
        if self.zenapikey:
            # Concatenate the strings with a colon
            concatenated_key = f"{self.username}:{self.zenapikey}"
            # Encode the concatenated string in Base64
            if not self.username:
                raise ValueError("Username must be provided when using zenapikey.")
            encoded_zen_key = base64.b64encode(concatenated_key.encode()).decode()
            return {
                'Authorization': f'ZenApiKey {encoded_zen_key}' ,
                'Content-Type': 'application/json; charset=UTF-8', 
                'accept': 'application/json; charset=UTF-8'
            }
        elif self.client_id:
            if not self.client_id or not self.client_secret or not self.token_url:
                raise ValueError("All three parameters are required for OpenId authentication: 'client_id', 'client_secret' and 'token_url'.")
            data = {
                'grant_type': 'client_credentials',
                'scope':       self.scope,
            }
            auth = requests.auth.HTTPBasicAuth(self.client_id, self.client_secret)
            if self.verify_ssl:
                response = requests.post(self.token_url, data=data, auth=auth, verify=self.cacert)
            else:
                response = requests.post(self.token_url, data=data, auth=auth, verify=False)
            response.raise_for_status() # raise an HTTPError if the request failed
            token_data = response.json()
            access_token = token_data['access_token']
            return {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json; charset=UTF-8',
                'accept': 'application/json; charset=UTF-8'
            }
        elif self.username and self.password:
            concatenated_key = f"{self.username}:{self.password}"
            encoded_user_cred = base64.b64encode(concatenated_key.encode()).decode()
            return { 
                'Authorization': f'Basic {encoded_user_cred}',
                'Content-Type': 'application/json; charset=UTF-8',
                'accept': 'application/json; charset=UTF-8'
            }
        else:
            raise ValueError("Either username and password, bearer token, or zenapikey must be provided.")

    def get_session(self):
        """
        Creates and returns a requests Session object configured with SSL settings
        """ 
        session = requests.Session()
        logging.info("Verify SSL: " + str(self.verify_ssl))
        if self.odm_url.startswith('https') and self.verify_ssl:
            session.verify = True
            session.mount('https://', CustomHTTPAdapter(certfile = self.ssl_cert_path))
        else:
            import urllib3
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            session.verify = False
        
        headers = self.get_auth()
        session.headers.update(headers)
        logging.info(f"Session created with URL: {self.odm_url}, Runtime URL: {self.odm_url_runtime} with headers: {session.headers}")
#        print("Session created with headers:", session.headers)
        
        return session