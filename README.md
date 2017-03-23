Python OnTrac API Module
============================

What is it?
-----------

A light wrapper around OnTrac's Webservice API.

Methods
-------------

### Init

Params:

| Name | Required | Description |
| ---- | ----- | ---- |
| account | true | OnTrac account username |
| password | true | OnTrac account password |
| production | false | Use OnTrac Production environment |

```python
from ontrac.service import OnTracService
service = OnTracService('37', 'testpass', False)
```

### zips ###

Retrieve zip codes serviced by OnTrac, optionally listing those updated since last_update

Params:

| Name | Required | Description |
| ---- | ----- | ---- |
| last_update | false | return zips updated since |

```python
from datetime import datetime
service.zips(datetime.strptime('2015-01-01', '%Y-%m-%d'))
```

Returns:

```python
[
    {
        "palletizedServiced": "1",
        "pickupServiced": "1",
        "saturdayServiced": "0",
        "sortCode": "DIA",
        "zipCode": "80002"
    },
    {
        "palletizedServiced": "1",
        "pickupServiced": "1",
        "saturdayServiced": "0",
        "sortCode": "DIA",
        "zipCode": "80003"
    },
    {
        "palletizedServiced": "1",
        "pickupServiced": "1",
        "saturdayServiced": "0",
        "sortCode": "DIA",
        "zipCode": "80017"
    }
]
```

### create_shipments ###

Create shipment in OnTrac

Params:

Name | Required | Description
---- | ----- | ----
shipments | true | array of shipments to send to OnTrac, in the following format:

```python
{
	'uid': 'unique id',
	'from': {                                     # required
		'name': 'name',                           # required
		'addr1': 'address 1',                     # required
		'addr2': 'address 2',
		'addr3': 'address 3',
		'city': 'city',                           # required
		'state': 'ST',                            # required
		'zip': 'postal',                          # required
		'contact': 'contact name',
		'phone': 'phone number',                  # required
	},
	'to': {
		'name': 'name',                           # required
		'addr1': 'address 1',                     # required
		'addr2': 'address 2',
		'addr3': 'address 3',
		'city': 'city',                           # required
		'state': 'ST',                            # required
		'zip': 'postal',                          # required
		'contact': 'contact name',
		'phone': 'phone number',                  # required
	},
	'service': 'S',                               # required
	'signature': False,
	'residential': True,
	'saturday': False,
	'declared': 500,
	'cod': 0,
	'cod_type': 'NONE',
	'weight': 1,                                  # required
	'bill_to': 0,
	'instructions': '',
	'reference': 'customer reference number',
	'reference2': None,
	'reference3': None,
	'tracking': None,
	'dimensions': {
		'length': 1,
		'width': 1,
		'height': 1,
	},
	'label_type': 1,
	'ship_email': None,
	'del_email': None,
	'ship_date': datetime.today(),
}
```

Example:

```python
from_addr = {'name': 'Rich Person', 'addr1': '123 Rich st', 'city': 'Beverly Hills', 'state': 'CA', 'zip': '90210', 'phone': '8005551212'}
to_addr = {'name': 'Hollywood Person', 'addr1': '456 Hollywood Bl', 'city': 'Hollywood', 'state': 'CA', 'zip': '90028', 'phone': '8005551212'}
service.create_shipments([{'from': from_addr, 'to': to_addr, 'service': 'C', 'weight': 1}])
```

Returns:

```python
[
    {
        "BilledWeight": "1",
        "CommitTime": "17:00:00",
        "Error": None,
        "ExpectedDeliveryDate": "20160104",
        "FuelChrg": "0",
        "Label": None,
        "RateZone": "2",
        "ServiceChargeDetails": {
            "AdditionalCharges": "1.75",
            "BaseCharge": "6.59",
            "CODCharge": "0",
            "DeclaredCharge": "0",
            "SaturdayCharge": "0"
        },
        "ServiceChrg": "8.34",
        "SortCode": "COM",
        "TariffChrg": "8.64",
        "TotalChrg": "8.34",
        "Tracking": "D10010863246611",
        "TransitDays": "1",
        "UID": None
    }
]
```

### shipment_details ###

Track shipment or get shipment details from OnTrac.

Params:

Name | Required | Description
---- | ----- | ----
tracking_numbers | true | List of tracking numbers for shipments
request_type | false | "details" or "track", for which type of data to return. Defaults to "details"
logo_format | false | OnTrac logo image format for track call
sig_format | false | Signature image format for track call

Example:

```python
service.shipment_details(['D10010863246611'])
```

Returns:

```python
{
    "Delivered": "false",
    "FuelCharge": "0",
    "Residential": "true",
    "ServiceCharge": "8.34",
    "TotalChrg": "8.34",
    "Tracking": "D10010863246611",
    "Weight": "1"
}
```

Example:

```python
service.shipment_details(['D10010863246611'], request_type='track')
```

Returns:

```python
{
    "Addr1": "456 HOLLYWOOD BL",
    "Addr2": None,
    "Addr3": None,
    "City": "HOLLYWOOD",
    "Contact": None,
    "Delivered": "false",
    "Error": None,
    "Events": {
        "Event": {
            "City": "COMMERCE",
            "Description": "DATA ENTRY",
            "EventTime": "2015-12-31T10:06:12.51",
            "Facility": "Commerce",
            "State": "CA",
            "Status": "XX",
            "Zip": "90040"
        }
    },
    "Exp_Del_Date": "2016-01-04T00:00:00",
    "FuelCharge": "0",
    "Name": "HOLLYWOOD PERSON",
    "POD": None,
    "Reference": None,
    "Reference2": None,
    "Reference3": None,
    "Residential": "true",
    "Service": "C",
    "ServiceCharge": "8.34",
    "ShipDate": "2015-12-31T00:00:00",
    "Signature": None,
    "State": "CA",
    "TotalChrg": "8.34",
    "Tracking": "D10010863246611",
    "Weight": "1",
    "Zip": "90028"
}
```

### rates ###

Get shipment rates

Params:

Name | Required | Description
---- | ----- | ----
packages | true | array of packages to send to OnTrac, in the following format:

```python
{
	'uid': 'unique id',
	'from_zip': 'postal',       # required
	'to_zip': 'postal',         # required
	'residential': True,
	'cod': 0,
	'saturday', False,
	'declared': 0,
	'weight': 1,                 # required
	'dimensions': {
		'length': 1,
		'width': 1,
		'height': 1,
	},
	'service': None,
	'letter': 0,
}
```

Example:

```python
package = {'from_zip': '90210', 'to_zip': '90028', 'weight': '1'}
service.rates([package])
```

Returns:

```python
[
    {
        "COD": "0",
        "DIM": {
            "Height": "0",
            "Length": "0",
            "Width": "0"
        },
        "Declared": "0",
        "Delzip": "90028",
        "Error": None,
        "PUZip": "90210",
        "Rates": {
            "Rate": [
                {
                    "BilledWeight": "1",
                    "CommitTime": "17:00:00",
                    "ExpectedDeliveryDate": "20160101",
                    "FuelCharge": "0",
                    "GlobalRate": "24.31",
                    "RateZone": "2",
                    "Service": "C",
                    "ServiceCharge": "8.34",
                    "ServiceChargeDetails": {
                        "AdditionalCharges": "1.75",
                        "BaseCharge": "6.59",
                        "CODCharge": "0",
                        "DeclaredCharge": "0",
                        "SaturdayCharge": "0"
                    },
                    "TotalCharge": "8.34",
                    "TransitDays": "1"
                },
                {
                    "BilledWeight": "1",
                    "CommitTime": "12:00:00",
                    "ExpectedDeliveryDate": "20160101",
                    "FuelCharge": "0",
                    "GlobalRate": "48.85",
                    "RateZone": "0",
                    "Service": "G",
                    "ServiceCharge": "31.5",
                    "ServiceChargeDetails": {
                        "AdditionalCharges": "1.75",
                        "BaseCharge": "29.75",
                        "CODCharge": "0",
                        "DeclaredCharge": "0",
                        "SaturdayCharge": "0"
                    },
                    "TotalCharge": "31.5",
                    "TransitDays": "1"
                },
                {
                    "BilledWeight": "1",
                    "CommitTime": "14:00:00",
                    "ExpectedDeliveryDate": "20160101",
                    "FuelCharge": "0",
                    "GlobalRate": "39.38",
                    "RateZone": "0",
                    "Service": "S",
                    "ServiceCharge": "22.5",
                    "ServiceChargeDetails": {
                        "AdditionalCharges": "1.75",
                        "BaseCharge": "20.75",
                        "CODCharge": "0",
                        "DeclaredCharge": "0",
                        "SaturdayCharge": "0"
                    },
                    "TotalCharge": "22.5",
                    "TransitDays": "1"
                }
            ]
        },
        "Residential": "true",
        "SaturdayDel": "true",
        "UID": None,
        "Weight": "1"
    }
]
```

### request_pickup ###

Request a pickup for a package

Params:

Name | Required | Description
---- | ----- | ----
pickup_info | true | Dictionary of pickup info to send to OnTrac, in the following format:

```python
{
	'date': datetime.today(),
	'earliest_time': '13:00:00',       # required
	'latest_time': '16:00:00',        # required
	'location_name': '',
	'addr1': 'address',               # required
	'city', 'city',                   # required
	'state': 'ST',                    # required
	'zip': 'postal',                  # required
	'dest_zip': 'postal',
	'instructions': None,
	'phone': 'phone number',          # required
	'contact': 'contact name',        # required
}
```

Example:

```python
service.request_pickup({'earliest_time': '14:00:00', 'latest_time': '16:00:00', 'addr1': '123 Rich st', 'city': 'Beverly Hills', 'state': 'CA', 'zip': '90210', 'dest_zip': '90028', 'phone': '8005551212', 'contact': 'Rich Person'})
```

Returns:

```python
'551733303'
```
