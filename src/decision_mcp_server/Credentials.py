import requests
from requests.adapters import HTTPAdapter
import ssl
from validator_collection import  checkers
import base64
import logging
import json
import time
import uuid
import hashlib
import base64
from datetime import datetime, timedelta


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
    jwt_cert_password : str, optional
        Password to decrypt the private key certificate for PKJWT authentication. Only needed if the certificate is password-protected.
    debug : bool, optional
        Whether to enable HTTP debug logging. Defaults to False.

    Methods:
    --------
    get_auth():
        Returns the appropriate authentication headers based on the provided credentials.
    get_session():
        Creates and returns a requests Session object configured with SSL settings.
    """
    def __init__(self, odm_url, odm_url_runtime=None, token_url=None, scope='openid', client_id=None, client_secret=None, jwt_cert_path=None, jwt_public_cert_path=None, jwt_cert_password=None, username=None, password=None, zenapikey=None, verify_ssl=True, ssl_cert_path=None, debug=False):

        # Get logger for this class with explicit name to ensure consistency
        self.logger = logging.getLogger("decision_mcp_server.Credentials")
        self.odm_url=odm_url.rstrip('/')
        if odm_url_runtime is not None:
           self.logger.info("Using provided runtime URL: " + odm_url_runtime)
           self.odm_url_runtime=odm_url_runtime.rstrip('/')  
        else:
            self.odm_url_runtime=self.odm_url
                # Check if the URL ends with 'res' and replace it with 'DecisionService'
            if self.odm_url_runtime.endswith('res'):
                self.odm_url_runtime=self.odm_url_runtime[:-3] + 'DecisionService'
            self.logger.info("No runtime URL provided, using odm_url as root runtime URL."+self.odm_url_runtime)
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
        self.jwt_cert_path = jwt_cert_path
        self.jwt_public_cert_path = jwt_public_cert_path
        self.jwt_cert_password = jwt_cert_password
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
            if not self.client_id or not self.token_url:
                raise ValueError("Both 'client_id' and 'token_url' are required for OpenId authentication.")
            
            # Check if we're using PWJWT (certificate-based) or client_secret
            if self.jwt_cert_path:
                from cryptography import x509
                from cryptography.hazmat.backends import default_backend
                from cryptography.hazmat.primitives import serialization
                # Ensure both private and public certificates are provided
                if not self.jwt_public_cert_path:
                    raise ValueError("Both 'jwt_cert_path' and 'jwt_public_cert_path' are required for PWJWT authentication.")
                
                # PWJWT authentication using certificate
                # Note: PyJWT package is required for PWJWT authentication
                # If you get an error, install it with: pip install PyJWT
                try:
                    # Try to import PyJWT dynamically
                    # pylint: disable=import-outside-toplevel
                    # type: ignore
                    import jwt  # type: ignore # noqa
                except ImportError:
                    raise ImportError("PyJWT package is required for PWJWT authentication. Install with 'pip install PyJWT'.")
                
                # Read the private key from the certificate file
                try:
                    with open(self.jwt_cert_path, 'r') as cert_file:
                        private_key_data = cert_file.read()
                    
                    # If a password is provided, decrypt the private key
                    if self.jwt_cert_password:
                        from cryptography.hazmat.primitives.serialization import load_pem_private_key
                        from cryptography.hazmat.primitives.serialization import Encoding, PrivateFormat, NoEncryption
                        
                        try:
                            # Load the encrypted private key
                            key_obj = load_pem_private_key(
                                private_key_data.encode(),
                                password=self.jwt_cert_password.encode(),
                                backend=default_backend()
                            )
                            
                            # Convert back to PEM format (unencrypted for use with PyJWT)
                            private_key = key_obj.private_bytes(
                                encoding=Encoding.PEM,
                                format=PrivateFormat.PKCS8,
                                encryption_algorithm=NoEncryption()
                            ).decode('utf-8')
                            
                            self.logger.info("Successfully decrypted password-protected certificate")
                        except Exception as e:
                            raise ValueError(f"Failed to decrypt certificate with provided password: {str(e)}")
                    else:
                        # Use the key as-is if no password
                        private_key = private_key_data
                except FileNotFoundError:
                    raise ValueError(f"Certificate file not found at path: {self.jwt_cert_path}")
                except IOError as e:
                    raise ValueError(f"Error reading certificate file: {str(e)}")
                
                # Create JWT token with required claims
                now = int(time.time())
                exp_time = now + 3600  # Token valid for 1 hour
                
                payload = {
                    'iss': self.client_id,  # Issuer is the client_id
                    'sub': self.client_id,  # Subject is also the client_id for client credentials
                    'aud': self.token_url,  # Audience is the token endpoint
                    'exp': exp_time,        # Expiration time
                    'iat': now,             # Issued at time
                    'jti': str(uuid.uuid4()) # Unique identifier for the JWT
                }
                
                try:
                    # Calculate the certificate thumbprint from the public certificate
                    try:
                        with open(self.jwt_public_cert_path, 'rb') as cert_file:
                            cert_data = cert_file.read()
                        
                        # Load the certificate
                        if b"BEGIN CERTIFICATE" in cert_data:
                            cert = x509.load_pem_x509_certificate(cert_data, default_backend())
                        else:
                            cert = x509.load_der_x509_certificate(cert_data, default_backend())
                        
                        # Calculate SHA-1 thumbprint (x5t)
                        sha1_hash = hashlib.sha1(cert.public_bytes(encoding=serialization.Encoding.DER)).digest()
                        sha1_b64 = base64.urlsafe_b64encode(sha1_hash).decode('utf-8').rstrip('=')
                        

                        # Calculate SHA-256 thumbprint
                        sha256_hash = hashlib.sha256(cert.public_bytes(encoding=serialization.Encoding.DER)).digest()
                        sha256_b64 = base64.urlsafe_b64encode(sha256_hash).decode('utf-8').rstrip('=')
                        
                        # Add thumbprints to JWT header
                        headers = {
                            'x5t': sha1_b64     # Use the calculated SHA-1 thumbprint
                        }
                        self.logger.debug(f"Using calculated x5t from public certificate: {sha1_b64}")
                    except Exception as e:
                        # Don't fallback to hardcoded value, raise an error instead
                        raise ValueError(f"Error calculating certificate thumbprint from public certificate: {str(e)}")
                    
                    # Sign the JWT with the private key and include headers
                    encoded_jwt = jwt.encode(payload, private_key, algorithm='RS256', headers=headers)
                    self.logger.info("JWT token created successfully.");   
                    self.logger.debug("msg encoded JWT "+encoded_jwt)                # Prepare the token request with the JWT assertion
                    data = {
                        'grant_type': 'client_credentials',
                        'scope': self.scope,
                        'client_assertion_type': 'urn:ietf:params:oauth:client-assertion-type:jwt-bearer',
                        'client_assertion': encoded_jwt
                    }
                    
                    # Make the token request without auth header (the JWT is the auth)
                    if self.verify_ssl:
                        response = requests.post(self.token_url, data=data, verify=self.cacert)
                    else:
                        response = requests.post(self.token_url, data=data, verify=False)
                except Exception as e:
                    raise ValueError(f"Error creating or sending JWT token: {str(e)}")
            else:
                # Standard OpenID client_secret authentication
                if not self.client_secret:
                    if self.jwt_public_cert_path:
                        raise ValueError("Both 'jwt_cert_path' and 'jwt_public_cert_path' are required for PWJWT authentication.")
                    else:
                        raise ValueError("Either 'client_secret' or 'jwt_cert_path' is required for OpenId authentication.")
                
                data = {
                    'grant_type': 'client_credentials',
                    'scope': self.scope,
                }
                auth = requests.auth.HTTPBasicAuth(self.client_id, self.client_secret)
                if self.verify_ssl:
                    response = requests.post(self.token_url, data=data, auth=auth, verify=self.cacert)
                else:
                    response = requests.post(url=self.token_url, data=data, auth=auth, verify=False)
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
        self.logger.info("Verify SSL: " + str(self.verify_ssl))
        if self.odm_url.startswith('https') and self.verify_ssl:
            session.verify = True
            session.mount('https://', CustomHTTPAdapter(certfile = self.ssl_cert_path))
        else:
            import urllib3
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            session.verify = False
        
        headers = self.get_auth()
        session.headers.update(headers)
        self.logger.debug(f"Session created with URL: {self.odm_url}, Runtime URL: {self.odm_url_runtime} with headers: {session.headers}")        
        return session