
# DineroAPI

## Description

`DineroAPI` is a Python wrapper for the Dinero API, providing easy-to-use methods for interacting with various endpoints of the Dinero accounting system. This library simplifies tasks such as creating invoices, managing contacts, uploading files, and more, by abstracting the complexities of direct API calls.

## Dependencies

- requests
- jsonschema

Install the required dependencies using pip:

```sh
pip install requests jsonschema
```

## Usage

For details about the available endpoints and their parameters, refer to the official [Dinero API documentation](https://api.dinero.dk/openapi/index.html).

### Initialization

To start using the DineroAPI, create an instance of the `DineroAPI` class with your API credentials and optionally set the organization ID.

```python
from DineroAPI import DineroAPI

api_key = 'your_api_key'
client_id = 'your_client_id'
client_secret = 'your_client_secret'
organization_id = 'your_organization_id'

dinero = DineroAPI(api_key, client_id, client_secret, org=organization_id)
```

### Example 1: List Accounting Years

Retrieve and print all accounting years for the organization.

```python
accounting_years = dinero.AccountingYear.list(pretty=True)
```

### Example 2: Create an Invoice

Create a new draft invoice and optionally book it.

```python
invoice_data = {
    "contactGuid": "contact_guid",
    "date": "2024-07-01",
    "description": "Invoice description",
    "lines": [
        {
            "description": "Product 1",
            "quantity": 1,
            "unitPrice": 100.0
        }
    ]
}

response = dinero.Invoice.create(invoice_data, auto_book=True)
print(response)
```

### Example 3: List Contacts

Retrieve and print a list of contacts.

```python
contacts = dinero.Contact.list(pretty=True)
```

### Example 4: Upload a File

Upload a file to the Dinero file archive.

```python
response = dinero.File.upload('path/to/your/file.pdf')
print(response)
```

### Example 5: List Entries with Changes

Retrieve a list of entries that have changed within a specific date range.

```python
changes_data = {
    "changesFrom": "2024-07-10T00:00:00Z",
    "changesTo": "2024-07-11T23:59:59Z",
    "includePrimo": True
}

changes = dinero.Entry.list_changes(pretty=True, params=changes_data)
```

### Example 6: Get Contact's State of Account

Get the income, expenses, and related entries for a contact in the given period.

```python
contact_guid = 'contact_guid'
state_params = {
    "from": "2024-01-01T00:00:00Z",
    "to": "2024-12-31T23:59:59Z",
    "hideClosed": False
}

state_of_account = dinero.Contact.State.get(contact_guid, params=state_params)
dinero.print_pretty(state_of_account)
```

## Debugging

Enable debugging by setting the `debug` parameter to `True` when initializing the `DineroAPI` instance. This will print detailed information about each request and response.

```python
dinero = DineroAPI(api_key, client_id, client_secret, org=organization_id)
dinero.debug = True
```

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
