from pathlib import Path
import json
import pandas as pd

path = Path(r"C:\Users\Public\ZenGarden\Crystal_Ball_6_Years_Reduced_Tech\data\Crystal_Ball\set_technologies\set_conversion_technologies\set_retrofitting_technologies")

# Get a list of only directories
folders = [f.name for f in path.iterdir() if f.is_dir()]
removed_carriers = ["ammonia",
                    "biomass",
                    "biomethane",
                    "carbon",
                    "clinker",
                    "crude_oil",
                    "diesel",
                    "district_heat",
                    "fuel_for_cement",
                    "gasoline",
                    "hydrogen",
                    "kerosene",
                    "methanol",
                    "naphtha",
                    "natural_gas_industry",
                    "olefin",
                    "passenger_mileage",
                    "primary_steel",
                    "secondary_steel",
                    "shipping",
                    "truck_mileage",
                    "waste",
                    "wet_biomass"
                    ]
Remaining_Tech_Dict = {}
Removed_Tech_Dict = {}

for technology in folders:
    print(technology)
    f_path = path / technology / "attributes.json"
    if f_path.exists():
        with open(f_path, "r") as f:
            attributes = json.load(f)
            input = attributes.get("input_carrier",{}).get("default_value",[])
            output = attributes.get("output_carrier", {}).get("default_value", [])
            reference = attributes.get("reference_carrier", {}).get("default_value", [])

            if not any(item in removed_carriers for item in input + output + reference):
                Remaining_Tech_Dict[technology] = {
                    "input_carrier": {str(input)},
                    "output_carrier": {str(output)},
                    "reference_carrier": {str(reference)}
                }
            else:
                Removed_Tech_Dict[technology] = {
                    "input_carrier": {str(input)},
                    "output_carrier": {str(output)},
                    "reference_carrier": {str(reference)}
                }

print("Remaining_Tech")
df = pd.DataFrame(Remaining_Tech_Dict)
with pd.option_context('display.max_rows', None, 'display.max_columns', None):
    print(df.columns)

print("Removed_Tech")
df = pd.DataFrame(Removed_Tech_Dict)
with pd.option_context('display.max_rows', None, 'display.max_columns', None):
    print(df.columns)