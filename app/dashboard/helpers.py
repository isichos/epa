
from typing import Dict, List, Optional, TypedDict, Union
import logging

logger = logging.getLogger(__name__)

def storage_asset_to_list(assets_results_json):
    """
    bring all storage subassets one level up to show their flows.
    restructure the main json dict to contain storage 
    'charging power','discharging power' and 'capacity' in the same level as storage.
    """
    if 'energy_storage' in assets_results_json.keys():
        for storage_asset in assets_results_json['energy_storage']:
            for subasset in storage_asset.values():
                if isinstance(subasset, dict) and 'flow' in subasset.keys():
                    subasset['energy_vector'] = storage_asset['energy_vector']
                    subasset['label'] = storage_asset['label']+subasset['label']
                    assets_results_json['energy_storage'].append(subasset)


def kpi_scalars_list(kpi_scalar_values_dict, KPI_SCALAR_UNITS, KPI_SCALAR_TOOLTIPS):
    return (
        [
            {
                'kpi': key.replace('_',' '),
                'value': round(val, 3) if 'currency/kWh' in KPI_SCALAR_UNITS[key] else round(val,2),
                'unit': KPI_SCALAR_UNITS[key],
                'tooltip': KPI_SCALAR_TOOLTIPS[key]
            }
            if key in KPI_SCALAR_UNITS.keys()
            else 
            {
                'kpi': key.replace('_',' '),
                'value': round(val, 3),
                'unit': 'N/A',
                'tooltip': ''
            }
            for key, val in kpi_scalar_values_dict.items()
        ]
    )



class ScalarMatrixObject(TypedDict):
    annual_total_flow: Union[None,float]
    average_flow: Union[None,float]
    installed_capacity: Union[None,float]
    optimized_add_cap: Union[None,float]
    peak_flow: Union[None,float]
    total_emissions: Union[None,float]
    total_flow: Union[None,float]
    unit: str


class AssetBarData(TypedDict):
    """the expected return dictionary per asset to be plotted as a bar chart"""
    label: str
    optimizedAddCap: Union[None,float]
    unit: str


def get_optimized_cap_data(kpi_scalars_matrix_dict: Dict[str,ScalarMatrixObject]) -> List[AssetBarData]:
    aggregated_optimized_caps = list()
    try:
        for asset, asset_kpis in kpi_scalars_matrix_dict.items():
            if (asset_kpis is None) or (not isinstance(asset_kpis, Dict)):
                # there are no data to add in the list
                continue

            asset_data: Union[AssetBarData, None] = extract_asset_data(asset, asset_kpis)
            if asset_data:
                aggregated_optimized_caps.append(asset_data)
        return aggregated_optimized_caps
    except Exception as ex:
        logger.info(f"get_optimized_cap_data exception: {ex}")
        return []


def extract_asset_data(asset: str, asset_dict: ScalarMatrixObject):
    try:
        if (all(key in asset_dict.keys() for key in ("optimized_add_cap", "unit")) 
            and asset_dict["optimized_add_cap"]!=None):
            rounded_optimized_add_cap = round(asset_dict["optimized_add_cap"], 2)
            return AssetBarData(
                label=asset,
                optimizedAddCap=rounded_optimized_add_cap, 
                unit=asset_dict["unit"]
            )
        else:
            return None
    except:
        return None