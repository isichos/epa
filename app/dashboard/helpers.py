
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



class AssetResults(TypedDict):
    """Note: i didn't know if the key, value pairs are optional.
    Does MVS always return a list, even if there are no asset of a specific type?
    If yes is the answer, then we can safely remove the `Optional` here.
    """
    energy_consumption: Optional[List[Dict]]
    energy_conversion: Optional[List[Dict]]
    energy_production: Optional[ List[Dict]]
    energy_providers: Optional[List[Dict]]
    energy_storage: Optional[List[Dict]]


class AssetBarData(TypedDict):
    """the expected return dictionary per asset to be plotted as a bar chart"""
    label: str
    optimizedAddCap: float
    unit: str

def get_optimized_cap_data(assets_results: AssetResults) -> List[AssetBarData]:
    storage_asset_to_list(assets_results)
    aggregated_optimized_caps = list()
    try:
        for key, assets_list in assets_results.items():
            current_type = key
            if (assets_list is None) or (not isinstance(assets_list, List)):
                # there are no data to add in the list
                continue
            for asset in assets_list:
                asset_data: Union[AssetBarData, None] = extract_asset_data(asset)
                if asset_data:
                    aggregated_optimized_caps.append(asset_data)
        return aggregated_optimized_caps
    except Exception as ex:
        logger.info(f"get_optimized_cap_data exception: {ex}")
        return []



def extract_asset_data(asset_dict: Dict):
    try:
        if (all(key in asset_dict.keys() for key in ("optimizedAddCap", "label"))
            and all(key in asset_dict["optimizedAddCap"] for key in ("value", "unit"))):
            return AssetBarData(
                label=asset_dict["label"], 
                optimizedAddCap=asset_dict["optimizedAddCap"]["value"], 
                unit=asset_dict["optimizedAddCap"]["unit"]
            )
        else:
            return None
    except:
        return None