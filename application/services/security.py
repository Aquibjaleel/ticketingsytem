import os
import json
from cryptography.fernet import Fernet
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

class SecureConfig:
    def __init__(self, vault_url=None):
        self.vault_url = vault_url or os.environ.get("AZURE_KEYVAULT_URL")
        self.master_key = None
        
        if self.vault_url:
            try:
                # Attempt to connect to Azure
                credential = DefaultAzureCredential()
                self.client = SecretClient(vault_url=self.vault_url, credential=credential)
                # Test the connection by fetching the key
                self.master_key = self.client.get_secret("flicket-master-key").value.encode()
            except Exception as e:
                print(f"Vault Unavailable: {e}. Falling back to Environment/JSON.")

    def decrypt(self, encrypted_blob):
        """Only decrypts if we successfully grabbed the Master Key."""
        if not self.master_key or not encrypted_blob:
            return None
        try:
            f = Fernet(self.master_key)
            return f.decrypt(encrypted_blob.encode()).decode()
        except Exception:
            return None