from datetime import datetime
import httpx as requests
import json
# from requests.exceptions import HTTPError
from epa.settings import PROXY_CONFIG, MVS_POST_URL, MVS_GET_URL
from dashboard.models import AssetsResults, KPICostsMatrixResults, KPIScalarResults
from projects.constants import DONE, PENDING, ERROR
import logging

logger = logging.getLogger(__name__)


def mvs_simulation_request(data: dict):

    headers = {'content-type': 'application/json'}
    payload = json.dumps(data)

    try:
        response = requests.post(MVS_POST_URL, data=payload, headers=headers, proxies=PROXY_CONFIG, verify=False)

        # If the response was successful, no Exception will be raised
        response.raise_for_status()
    except requests.HTTPError as http_err:
        logger.error(f'HTTP error occurred: {http_err}')
        return None
    except Exception as err:
        logger.error(f'Other error occurred: {err}')
        return None
    else:
        logger.info('The simulation was sent successfully to MVS API.')
        return json.loads(response.text)


def mvs_simulation_check(token):
    try:
        response = requests.get(MVS_GET_URL+token, proxies=PROXY_CONFIG, verify=False)
        response.raise_for_status()
    except requests.HTTPError as http_err:
        logger.error(f'HTTP error occurred: {http_err}')
        return None
    except Exception as err:
        logger.error(f'Other error occurred: {err}')
        return None
    else:
        logger.info('Success!')
        return json.loads(response.text)


def check_mvs_simulation(simulation):
    if simulation.status == PENDING:
        response = mvs_simulation_check(token=simulation.mvs_token)
        try:
            simulation.status = response['status']
            simulation.errors = json.dumps(response['results'][ERROR]) if simulation.status == ERROR else None
            simulation.results = parse_mvs_results(simulation, response['results']) if simulation.status == DONE else None
        except:
            simulation.status = ERROR
            simulation.results = None

        simulation.elapsed_seconds = (datetime.now() - simulation.start_date).seconds
        simulation.end_date = datetime.now() if response['status'] in [ERROR, DONE] else None
        simulation.save()


def parse_mvs_results(simulation, response_results):
    data = json.loads(response_results)
    asset_key_list = ['energy_consumption', 'energy_conversion', 'energy_production', 
                        'energy_providers', 'energy_storage']

    if not set(asset_key_list).issubset(data.keys()):
        raise KeyError('There are missing keys from the received dictionary.')

    # Write Scalar KPIs to db
    KPIScalarResults.objects.create(scalar_values=json.dumps(data['kpi']['scalars']), simulation=simulation)
    # Write Cost Matrix KPIs to db
    KPICostsMatrixResults.objects.create(cost_values=json.dumps(data['kpi']['cost_matrix']), simulation=simulation)
    # Write Assets to db
    data_subdict={category:v for category,v in data.items() if category in asset_key_list}
    AssetsResults.objects.create(assets_list=json.dumps(data_subdict), simulation=simulation)

