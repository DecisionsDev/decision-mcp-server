import requests
from requests.auth import HTTPBasicAuth
#from validator_collection import  checkers
import base64
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
    bearer_token : str, optional
        The bearer token for token-based authentication.
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
    def __init__(self, odm_url, odm_url_runtime=None, username=None, password=None, bearer_token=None, zenapikey=None, verify_ssl=True, ssl_cert_path=None, debug=False):

        self.odm_url=odm_url.rstrip('/') 
        if odm_url_runtime is not None:
           self.odm_url_runtime=odm_url_runtime.rstrip('/')  
        else:
            self.odm_url_runtime=self.odm_url
                # Check if the URL ends with 'res' and replace it with 'DecisionService'
            if self.odm_url_runtime.endswith('res'):
                self.odm_url_runtime=self.odm_url_runtime[:-3] + 'DecisionService'
#        if not checkers.is_url(self.odm_url):
#            raise ValueError("'"+self.odm_url+"' is not a valid URL")
        self.username = username
        self.password = password
        self.bearer_token = bearer_token
        self.zenapikey = zenapikey
        self.verify_ssl = verify_ssl
        self.ssl_cert_path = ssl_cert_path
        self.debug = debug

    def get_auth(self):
        if self.zenapikey:
            # Concatenate the strings with a colon
            concatenated_key = f"{self.username}:{self.zenapikey}"
            # Encode the concatenated string in Base64
            encoded_zen_key = base64.b64encode(concatenated_key.encode()).decode()
            return None,{
                'Authorization': f'ZenApiKey '+encoded_zen_key,
                'Content-Type': 'application/json; charset=UTF-8',
                'accept': 'application/json; charset=UTF-8'
            }
        elif self.bearer_token:
            return {
                'Authorization': f'Bearer {self.bearer_token}',
                'Content-Type': 'application/json; charset=UTF-8',
                'accept': 'application/json; charset=UTF-8'
            }
        elif self.username and self.password:
            return HTTPBasicAuth(self.username, self.password), {
                'Content-Type': 'application/json; charset=UTF-8',
                'accept': 'application/json; charset=UTF-8'
            }
        else:
            raise ValueError("Either username and password, bearer token, or zenapikey must be provided.")

    def get_session(self):
        """
        Creates and returns a requests Session object configured with SSL settings
        """

        
        if self.debug:
            enable_http_debug()
            
        session = requests.Session()
        
        if self.odm_url.startswith('https'):
            if self.verify_ssl:
                session.verify = self.ssl_cert_path if self.ssl_cert_path else True
            else:
                import urllib3
                urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
                session.verify = False
        
        auth, headers = self.get_auth()
        if auth:
            session.auth = auth
        session.headers.update(headers)
        
        return session