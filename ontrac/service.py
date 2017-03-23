from datetime import datetime
from urllib.parse import urlencode
from urllib import request
from collections import defaultdict, OrderedDict

from lxml import etree


class OnTracError(Exception):
	pass


class OnTracService(object):
	TEST_URL = 'https://www.shipontrac.net/OnTracTestWebServices/OnTracServices.svc/V2/{account}/{method}?{qs}'
	PRODUCTION_URL = 'https://www.shipontrac.net/OnTracWebServices/OnTracServices.svc/V2/{account}/{method}?{qs}'

	def __init__(self, account, password, production=True):
		if production:
			self.service_url = self.PRODUCTION_URL
		else:
			self.service_url = self.TEST_URL
		self.account = account
		self.password = password

	def build_payload(self, root_name, values):
		def build_payload_children(parent_node, values):
			for key, val in iter(values.items()):
				node = etree.SubElement(parent_node, key)
				if isinstance(val, dict):
					build_payload_children(node, val)
				elif isinstance(val, list):
					for item in val:
						if isinstance(item, dict):
							build_payload_children(node, item)
				elif isinstance(val, bool):
					node.text = 'true' if val else 'false'
				elif val is not None:
					node.text = str(val)

		root = etree.Element(root_name)
		build_payload_children(root, values)
		return etree.tostring(root, encoding='unicode')

	def etree_to_dict(self, t):
		d = {t.tag: {} if t.attrib else None}
		children = list(t)
		if children:
			dd = defaultdict(list)
			for dc in map(self.etree_to_dict, children):
				for k, v in dc.items():
					dd[k].append(v)
			d = {t.tag: {k: v[0] if len(v) == 1 else v for k, v in dd.items()}}
		if t.attrib:
			d[t.tag].update(('@' + k, v) for k, v in t.attrib.items())
		if t.text:
			text = t.text.strip()
			if children or t.attrib:
				if text:
					d[t.tag]['#text'] = text
			else:
				d[t.tag] = text
		return d

	def _call(self, method, qs={}, post_xml=None):
		if not qs:
			qs = {}
		qs.update({'pw': self.password})
		method_url = self.service_url.format(account=self.account, method=method, qs=urlencode(qs))

		if post_xml:
			# convert dict to xml
			req = request.Request(url=method_url,
				data=post_xml.encode('utf_8'),
				headers={'Content-Type': 'application/xml'})
		else:
			req = request.Request(url=method_url)
		response = request.urlopen(req)

		# read xml result
		xml_response = response.read().decode(response.info().get_param('charset') or 'utf-8')
		return self.etree_to_dict(etree.fromstring(xml_response))

	def zips(self, last_update=None):
		params = None
		if last_update:
			params = {'lastUpdate': last_update.strftime('%Y-%m-%d')}
		response = self._call('Zips', params)
		return response['OnTracZipResponse']['Zips']['Zip']

	def create_shipments(self, shipments):
		"""
		Shipment format:
			[] = {
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
		"""
		def convert_address(address):
			addr = OrderedDict([
				('Name', address['name']),
				('Addr1', address['addr1']),
				('Addr2', address.get('addr2')),
				('Addr3', address.get('addr3')),
				('City', address['city']),
				('State', address['state']),
				('Zip', address['zip']),
				('Contact', address.get('contact')),
				('Phone', address['phone']),
			])
			return addr

		def convert_from_address(address):
			addr = convert_address(address)
			del addr['Addr2']
			del addr['Addr3']
			return addr

		def convert_dim(dims):
			return {'Length': dims['length'], 'Width': dims['width'], 'Height': dims['height']}

		def convert_ship_date(ship_date):
			return ship_date.strftime('%Y-%m-%d')

		# build XML
		shipment_field_map = OrderedDict([
			('uid', {'field': 'UID', 'optional': True, 'default': None}),
			('from', {'field': 'shipper', 'optional': False, 'method': 'convert_from_address'}),
			('to', {'field': 'consignee', 'optional': False, 'method': 'convert_address'}),
			('service', {'field': 'Service', 'optional': False, 'validate': ['S', 'G', 'H', 'C']}),
			('signature', {'field': 'SignatureRequired', 'optional': True, 'default': False}),
			('residential', {'field': 'Residential', 'optional': True, 'default': True}),
			('saturday', {'field': 'SaturdayDel', 'optional': True, 'default': False}),
			('declared', {'field': 'Declared', 'optional': True, 'default': '0'}),
			('cod', {'field': 'COD', 'optional': True, 'default': '0'}),
			('cod_type', {'field': 'CODType', 'optional': True, 'default': 'NONE'}),
			('weight', {'field': 'Weight', 'optional': False}),
			('bill_to', {'field': 'BillTo', 'optional': True, 'default': '0'}),
			('instructions', {'field': 'Instructions', 'optional': True, 'default': None}),
			('reference', {'field': 'Reference', 'optional': True, 'default': None}),
			('reference2', {'field': 'Reference2', 'optional': True, 'default': None}),
			('reference3', {'field': 'Reference3', 'optional': True, 'default': None}),
			('tracking', {'field': 'Tracking', 'optional': True, 'default': None}),
			('dimensions', {'field': 'DIM', 'optional': True, 'default': {'Length': 0, 'Width': 0, 'Height': 0}, 'method': 'convert_dim'}),
			('label_type', {'field': 'LabelType', 'optional': True, 'default': 0, 'validate': [0, 1, 6, 7]}),
			('ship_email', {'field': 'ShipEmail', 'optional': True, 'default': None}),
			('del_email', {'field': 'DelEmail', 'optional': True, 'default': None}),
			('ship_date', {'field': 'ShipDate', 'optional': True, 'default': datetime.today().strftime('%Y-%m-%d'), 'method': 'convert_ship_date'}),
			('cargo_type', {'field': 'CargoType', 'optional': True, 'default': '0'}),
		])

		if not shipments:
			raise OnTracError('At least one shipment is required')

		body = {'Shipments': {'Shipment': []}}
		for shipment in shipments:
			item = OrderedDict()
			for field, field_map in iter(shipment_field_map.items()):
				if field not in shipment and not field_map['optional']:
					raise OnTracError('Field {} is required'.format(field))
				if 'validate' in field_map and field in shipment and shipment[field] not in field_map['validate']:
					raise OnTracError('Invalid value for {}: {}'.format(field, shipment[field]))
				if 'method' in field_map and field in shipment:
					try:
						item[field_map['field']] = locals()[field_map['method']](shipment[field])
					except KeyError as exc:
						raise OnTracError('Data error on {}: {} is required'.format(field, exc))
				elif 'default' in field_map:
					item[field_map['field']] = shipment.get(field, field_map['default'])
				elif field in shipment:
					item[field_map['field']] = shipment[field]

			body['Shipments']['Shipment'].append(item)
		response = self._call('shipments', post_xml=self.build_payload('OnTracShipmentRequest', body))
		if 'Error' in response['OnTracShipmentResponse'] and response['OnTracShipmentResponse']['Error']:
			raise OnTracError(response['OnTracShipmentResponse']['Error'])
		response_shipments = response['OnTracShipmentResponse']['Shipments']['Shipment']
		if not isinstance(response_shipments, list):
			response_shipments = [response_shipments]
		return response_shipments

	def shipment_details(self, tracking_numbers, request_type='details', logo_format=None, sig_format=None):
		params = {'tn': ','.join(tracking_numbers), 'requestType': request_type}
		if logo_format:
			params['logoFormat'] = logo_format
		if sig_format:
			params['sigFormat'] = sig_format
		response = self._call('shipments', params)
		if request_type == 'details':
			return response['OnTracUpdateResponse']['Shipments']['Shipment']
		return response['OnTracTrackingResult']['Shipments']['Shipment']

	def rates(self, packages):
		"""
		Package format:
			[] = {
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
		"""

		def convert_dim(dims):
			return '{}X{}X{}'.format(dims['length'], dims['width'], dims['height'])

		package_field_map = OrderedDict([
			('uid', {'field': 'UID', 'optional': True, 'default': ''}),
			('from_zip', {'field': 'PUZip', 'optional': False}),
			('to_zip', {'field': 'DelZip', 'optional': False}),
			('residential', {'field': 'Residential', 'optional': True, 'default': 'true'}),
			('cod', {'field': 'COD', 'optional': True, 'default': '0'}),
			('saturday', {'field': 'SaturdayDel', 'optional': True, 'default': 'true'}),
			('declared', {'field': 'Declared', 'optional': True, 'default': '0'}),
			('weight', {'field': 'Weight', 'optional': False}),
			('dimensions', {'field': 'DIM', 'optional': True, 'default': '0X0X0', 'method': 'convert_dim'}),
			('service', {'field': 'Service', 'optional': True, 'default': '', 'validate': ['S', 'G', 'H', 'C']}),
			('letter', {'field': 'Letter', 'optional': True, 'default': '0'}),
			('cargo_type', {'field': 'CargoType', 'optional': True, 'default': '0'}),
		])

		if not packages:
			raise OnTracError('At least one package is required')

		send_packages = []
		for package in packages:
			item = []
			for field, field_map in iter(package_field_map.items()):
				if field not in package and not field_map['optional']:
					raise OnTracError('Field {} is required'.format(field))
				if 'method' in field_map and field in package:
					try:
						item.append(locals()[field_map['method']](package[field]))
					except KeyError as exc:
						raise OnTracError('Data error on {}: {} is required'.format(field, exc))
				elif 'default' in field_map:
					item.append(package.get(field, field_map['default']))
				elif isinstance(package[field], bool):
					item.append('true' if package[field] else 'false')
				else:
					item.append(str(package[field]))
			send_packages.append(';'.join(item))
		params = {'packages': ','.join(send_packages)}
		response = self._call('rates', params)
		if 'Error' in response['OnTracRateResponse'] and response['OnTracRateResponse']['Error']:
			raise OnTracError(response['OnTracRateResponse']['Error'])
		response_shipments = response['OnTracRateResponse']['Shipments']['Shipment']
		if not isinstance(response_shipments, list):
			response_shipments = [response_shipments]
		return response_shipments

	def request_pickup(self, pickup_info):
		"""
		Pickup format:
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
		"""

		def convert_pickup_date(pickup_date):
			return pickup_date.strftime('%Y-%m-%d')

		pickup_field_map = OrderedDict([
			('date', {'field': 'Date', 'optional': True, 'default': datetime.today().strftime('%Y-%m-%d'), 'method': 'convert_pickup_date'}),
			('earliest_time', {'field': 'ReadyAt', 'optional': False}),
			('latest_time', {'field': 'CloseAt', 'optional': False}),
			('location_name', {'field': 'Name', 'optional': True, 'default': None}),
			('addr1', {'field': 'Address', 'optional': False}),
			('city', {'field': 'City', 'optional': False}),
			('state', {'field': 'State', 'optional': False}),
			('zip', {'field': 'Zip', 'optional': False}),
			('dest_zip', {'field': 'DelZip', 'optional': True, 'default': None}),
			('instructions', {'field': 'Instructions', 'optional': True, 'default': None}),
			('phone', {'field': 'Phone', 'optional': False}),
			('contact', {'field': 'Contact', 'optional': False}),
		])
		item = OrderedDict()
		for field, field_map in iter(pickup_field_map.items()):
			if field not in pickup_info and not field_map['optional']:
				raise OnTracError('Field {} is required'.format(field))
			if 'validate' in field_map and field in pickup_info and pickup_info[field] not in field_map['validate']:
				raise OnTracError('Invalid value for {}: {}'.format(field, pickup_info[field]))
			if 'method' in field_map and field in pickup_info:
				try:
					item[field_map['field']] = locals()[field_map['method']](pickup_info[field])
				except KeyError as exc:
					raise OnTracError('Data error on {}: {} is required'.format(field, exc))
			elif 'default' in field_map:
				item[field_map['field']] = pickup_info.get(field, field_map['default'])
			elif field in pickup_info:
				item[field_map['field']] = pickup_info[field]

		response = self._call('pickups', post_xml=self.build_payload('OnTracPickupRequest', item))
		if 'Error' in response['OnTracPickupResponse'] and response['OnTracPickupResponse']['Error']:
			raise OnTracError(response['OnTracPickupResponse']['Error'])
		return response['OnTracPickupResponse']['Tracking']
