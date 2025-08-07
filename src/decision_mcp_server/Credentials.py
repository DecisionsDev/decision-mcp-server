import requests
from validator_collection import  checkers
import base64
import logging
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
    def __init__(self, odm_url, odm_url_runtime=None, client_id=None, client_secret=None, username=None, password=None, zenapikey=None, verify_ssl=True, ssl_cert_path=None, debug=False):

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
        self.username = username
        self.password = password
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
            if not self.client_id or not self.client_secret:
                raise ValueError("Both client_id and client_secret must be provided for OpenID authentication.")
            # TODO Tobe implemented with OpenID Connect
            # For now, we will use a placeholder for the bearer token
            # In a real implementation, you would obtain a token from the OpenID provider
            bearer_token = self.client_id + ":" + self.client_secret

            return {
                'Authorization': f'Bearer {bearer_token}',
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
        if self.odm_url.startswith('https'):
            if self.verify_ssl:
                session.verify = self.ssl_cert_path if self.ssl_cert_path else True
            else:
                import urllib3
                urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
                session.verify = False
        
        headers = self.get_auth()

        session.headers.update(headers)
        logging.info(f"Session created with URL: {self.odm_url}, Runtime URL: {self.odm_url_runtime} with headers: {session.headers}")
#        print("Session created with headers:", session.headers)
        
        return session