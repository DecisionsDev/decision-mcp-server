import ssl
import socket
import certifi
import OpenSSL
from urllib.parse import urlparse

def extract_certificate_from_url(url: str, output_path: str = None) -> str:
    """
    Extract SSL certificate from a URL and optionally save it to a PEM file
    
    Args:
        url (str): The HTTPS URL to extract the certificate from
        output_path (str, optional): Path to save the PEM file. If None, returns the PEM content as string
        
    Returns:
        str: PEM certificate content
    """
    # Parse URL to get hostname
    parsed_url = urlparse(url)
    hostname = parsed_url.hostname
    port = parsed_url.port or 443

    # Create SSL context using system's trusted certificates
    context = ssl.create_default_context(cafile=certifi.where())
    
    try:
        with socket.create_connection((hostname, port)) as sock:
            with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                cert_bin = ssock.getpeercert(binary_form=True)
                x509 = OpenSSL.crypto.load_certificate(OpenSSL.crypto.FILETYPE_ASN1, cert_bin)
                pem_data = OpenSSL.crypto.dump_certificate(OpenSSL.crypto.FILETYPE_PEM, x509).decode('utf-8')
                
                if output_path:
                    with open(output_path, 'w') as f:
                        f.write(pem_data)
                
                return pem_data
    except Exception as e:
        raise Exception(f"Failed to extract certificate from {url}: {str(e)}")