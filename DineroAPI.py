import requests
from requests.auth import HTTPBasicAuth
from jsonschema import validate, ValidationError
import json
import os
from pathlib import Path

class DineroAPI:
    def __init__(self, api_key: str, client_id: str, client_secret: str, org=None):
        self.base_url = f'https://api.dinero.dk/v1'
        self.api_key = api_key
        self.client_id = client_id
        self.client_secret = client_secret
        self.org = org
        self.token = self._auth()
        self.debug = False
        self.AccountingYear = self.AccountingYear(self)
        self.Account = self.Account(self)
        self.Attachment = self.Attachment(self)
        self.Contact = self.Contact(self)
        self.Entry = self.Entry(self)
        self.Invoice = self.Invoice(self)
        self.Voucher = self.Voucher(self)
        self.File = self.File(self)

    def _auth(self):
        auth_url = 'https://authz.dinero.dk/dineroapi/oauth/token'
        data = {
            'grant_type': 'password',
            'scope': 'read write',
            'username': self.api_key,
            'password': self.api_key,
        }
        response = requests.post(auth_url, data=data, auth=HTTPBasicAuth(self.client_id, self.client_secret))
        response.raise_for_status()
        response_json = response.json()
        return response_json.get('access_token')

    def _request(self, method, endpoint, data=None, params=None, content_type='application/json'):
        if not self.org and endpoint not in ['organizations', 'health/startup']:
            raise ValueError("Organization ID is not set. Please set the organization ID to proceed.")

        base_url = f'{self.base_url}/{self.org}/' if self.org else f'{self.base_url}/'
        headers = {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': content_type,
        }
        url = base_url + endpoint
        response = requests.request(method, url, headers=headers, json=data, params=params)

        if self.debug:
            print("---------- DEBUG ----------")
            print(f"Requesting {method} {url}")
            print(f"Headers: {headers}")
            print(f"Data: {data}")
            print(f"Params: {params}")
            print(f"Response: {response.status_code} {response.text}")
            print("---------- DEBUG ----------")

        response.raise_for_status()
        return response.json() if response.content else {}
    
    def _validate(self, data, schema_prefix: str, func: str):
        schema_path = Path(__file__).parent / 'Schemas' / f'{schema_prefix}_{func}_schema.json'
        if not os.path.exists(schema_path):
            print(f"Schema file not found: {schema_path}")
            print("Validation skipped.")
            return
        with open(schema_path, 'r') as schema_file:
            schema = json.load(schema_file)
        try:
            validate(instance=data, schema=schema)
        except ValidationError as e:
            raise ValueError(f"Invalid data for {schema_prefix} {func}: {e.message}")
        
    def listOrgs(self):
        return self._request('GET', 'organizations')
    
    def checkHealth(self):
        return self._request('GET', 'health/startup')
    
    def print_pretty(self, data):
        if isinstance(data, dict):
            for key, value in data.items():
                print(f"{key}:")
                if isinstance(value, list):
                    for item in value:
                        print(json.dumps(item, indent=4))
                else:
                    print(json.dumps(value, indent=4))
        elif isinstance(data, list):
            for item in data:
                print(json.dumps(item, indent=4))
        else:
            print(json.dumps(data, indent=4))

    class AccountingYear:
        def __init__(self, api_instance):
            self.api_instance = api_instance
            self.endpoint = 'accountingyears'

        def list(self, pretty=False):
            if pretty:
                return self.api_instance.print_pretty(self.api_instance._request('GET', self.endpoint))
            else:
                return self.api_instance._request('GET', self.endpoint)

    class Account:
        def __init__(self, api_instance):
            self.api_instance = api_instance
            self.endpoint = 'accounts'
            self.schemaPrefix = 'account'

        def create(self, data, type='entry'):
            if type not in ['entry', 'deposit']:
                raise ValueError(f"Invalid account type: {type}")
            self.api_instance._validate(data, f"{self.schemaPrefix}_{type}", 'create')
            return self.api_instance._request('POST', f"{self.endpoint}/{type}", data=data)

        def list(self, pretty=False, params=None, type='entry'):
            if type not in ['entry', 'deposit', 'purchase']:
                raise ValueError(f"Invalid account type: {type}")
            self.api_instance._validate(params or {}, f"{self.schemaPrefix}_{type}", 'list')
            if pretty:
                return self.api_instance.print_pretty(self.api_instance._request('GET', f"{self.endpoint}/{type}", params=params))
            else:
                return self.api_instance._request('GET', f"{self.endpoint}/{type}", params=params)
    
    class Attachment:
        def __init__(self, api_instance):
            self.api_instance = api_instance
            self.endpoint = 'attachments'

        def bind(self, documentGuid: str, fileGuid: str, fileName: str):
            return self.api_instance._request('POST', f'{self.endpoint}/{documentGuid}/{fileGuid}/{fileName}')

        def delete(self, documentGuid: str, fileGuid: str):
            return self.api_instance._request('DELETE', f'{self.endpoint}/{documentGuid}/{fileGuid}')
        
    class Contact:
        def __init__(self, api_instance):
            self.api_instance = api_instance
            self.endpoint = 'contacts'
            self.schemaPrefix = 'contact'
            self.State = self.State(self.api_instance)

        def create(self, data):
            self.api_instance._validate(data, self.schemaPrefix, 'create')
            return self.api_instance._request('POST', self.endpoint, data=data)

        def update(self, contact_id: str, data):
            self.api_instance._validate(data, self.schemaPrefix, 'update')
            return self.api_instance._request('PUT', f'{self.endpoint}/{contact_id}', data=data)

        def delete(self, contact_id: str):
            return self.api_instance._request('DELETE', f'{self.endpoint}/{contact_id}')

        def get(self, contact_id: str):
            return self.api_instance._request('GET', f'{self.endpoint}/{contact_id}')
        
        def list(self, pretty=False, params=None):
            self.api_instance._validate(params or {}, self.schemaPrefix, 'list')
            if pretty:
                return self.api_instance.print_pretty(self.api_instance._request('GET', self.endpoint, params=params))
            else:
                return self.api_instance._request('GET', self.endpoint, params=params)
        
        class State:
            def __init__(self, api_instance):
                self.api_instance = api_instance
                self.endpoint = 'state-of-account'
                self.schemaPrefix = 'contact_state'

            def get(self, contact_guid: str, params=None):
                self.api_instance._validate(params or {}, self.schemaPrefix, 'get')
                return self.api_instance._request('GET', f'{self.endpoint}/{contact_guid}', params=params)

    class Entry:
        def __init__(self, api_instance):
            self.api_instance = api_instance
            self.endpoint = 'entries'
            self.schemaPrefix = 'entry'

        def list(self, pretty=False, params=None):
            self.api_instance._validate(params or {}, self.schemaPrefix, 'list')
            if pretty:
                return self.api_instance.print_pretty(self.api_instance._request('GET', self.endpoint, params=params))
            else:
                return self.api_instance._request('GET', self.endpoint, params=params)
            
        def listChanges(self, pretty=False, params=None):
            self.api_instance._validate(params or {}, self.schemaPrefix, 'list')
            if pretty:
                return self.api_instance.print_pretty(self.api_instance._request('GET', f'{self.endpoint}/changes', params=params))
            else:
                return self.api_instance._request('GET', f'{self.endpoint}/changes', params=params)

    class Invoice:
        def __init__(self, api_instance):
            self.api_instance = api_instance
            self.endpoint = 'invoices'
            self.schemaPrefix = 'invoice'

        def create(self, data, autoBook=False):
            self.api_instance._validate(data, self.schemaPrefix, 'create')
            response = self.api_instance._request('POST', self.endpoint, data=data)
            if autoBook:
                self.book(response.get('Guid'), response.get('Timestamp'))
            return response

        def update(self, invoice_id: str, data):
            self.api_instance._validate(data, self.schemaPrefix, 'update')
            return self.api_instance._request('PUT', f'{self.endpoint}/{invoice_id}', data=data)

        def delete(self, invoice_id: str, timestamp: str):
            return self.api_instance._request('DELETE', f'{self.endpoint}/{invoice_id}', data={'timestamp': timestamp})

        def get(self, invoice_id: str):
            return self.api_instance._request('GET', f'{self.endpoint}/{invoice_id}')
        
        def list(self, pretty=False, params=None):
            self.api_instance._validate(params or {}, self.schemaPrefix, 'list')
            if pretty:
                return self.api_instance.print_pretty(self.api_instance._request('GET', self.endpoint, params=params))
            else:
                return self.api_instance._request('GET', self.endpoint, params=params)
        
        def book(self, guid, timestamp):
            return self.api_instance._request('POST', f'{self.endpoint}/{guid}/book', data={'timestamp': timestamp})
        
    class Voucher:
        def __init__(self, api_instance):
            self.api_instance = api_instance
            self.endpoint = 'vouchers/manuel'
            self.schemaPrefix = 'voucher'

        def create(self, data, autoBook=False):
            self.api_instance._validate(data, self.schemaPrefix, 'create')
            response = self.api_instance._request('POST', self.endpoint, data=data)
            if autoBook:
                self.book(response.get('Guid'), response.get('Timestamp'))
            return response

        def update(self, voucher_id: str, data):
            self.api_instance._validate(data, self.schemaPrefix, 'update')
            return self.api_instance._request('PUT', f'{self.endpoint}/{voucher_id}', data=data)

        def delete(self, voucher_id: str, timestamp: str):
            return self.api_instance._request('DELETE', f'{self.endpoint}/{voucher_id}', data={'timestamp': timestamp})

        def get(self, voucher_id: str):
            return self.api_instance._request('GET', f'{self.endpoint}/{voucher_id}')
        
        def book(self, guid, timestamp: str):
            return self.api_instance._request('POST', f'{self.endpoint}/{guid}/book', data={'timestamp': timestamp})

    class File:
        def __init__(self, api_instance):
            self.api_instance = api_instance
            self.endpoint = 'files'
            self.schemaPrefix = 'file'

        def upload(self, file_path):
            with open(file_path, 'rb') as file:
                return self.api_instance._request('POST', self.endpoint, data=file, content_type='multipart/formdata')
        
        def list(self, pretty=False, params=None):
            self.api_instance._validate(params or {}, self.schemaPrefix, 'list')
            if pretty:
                return self.api_instance.print_pretty(self.api_instance._request('GET', self.endpoint, params=params))
            else:
                return self.api_instance._request('GET', self.endpoint, params=params)

        def download(self, file_guid: str, file_path):
            response = self.api_instance._request('GET', f'{self.endpoint}/{file_guid}', content_type='application/octet-stream')
            with open(file_path, 'wb') as file:
                file.write(response.content)
            return response
