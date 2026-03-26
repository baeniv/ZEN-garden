"""
This file implements the scenariotree class
reading, holding and processing the scenariotree information for a stochastic model
"""
from anytree import AnyNode, PreOrderIter
import json
import os
import pandas as pd
from toolz.functoolz import return_none


class ScenarioTree:
    """
    Class defining a scenariotree
    """
    def __init__(self,analysis):
        self.data = None
        self.root = None
        self.node_id_lookup = None
        self.scenariotree_data = self.get_scenariotree_data(analysis)

        self.json_to_anytree(self.scenariotree_data)
        self.leaf_nodes = {node.node_id: node for node in self.root.leaves}
        self.number_of_nodes = len(self.node_id_lookup)

    def json_to_anytree(self, node_data, parent=None, node_id_lookup=None):
        """
        Convert JSON-like dict to AnyTree nodes recursively.
        """
        # Create lookup dictionary once (for root call)
        if self.node_id_lookup is None:
            self.node_id_lookup = {}

        # Compute node-to-root path
        if parent is None:
            node2root_path = (node_data["node_id"],)
        else:
            node2root_path = (node_data["node_id"],) + parent.node2root_path

        # Create AnyTree node
        node = AnyNode(
            node_id=node_data["node_id"],
            year=node_data["year"],
            probability=node_data["probability"],
            state=node_data.get("state"),
            parent=parent,
            node2root_path=node2root_path
        )
        # Store node as root if root
        if node.is_root:
            self.root = node

        # Store node in lookup
        self.node_id_lookup[node.node_id] = node

        # Recursively process children
        for child in node_data.get("children", []):
            self.json_to_anytree(child, parent=node, node_id_lookup=node_id_lookup)

        return node

    def get_scenariotree_data(self, analysis):
        """ retrieves the scenariotree data

        :param config: config of optimization
        :return: data from scenariotree.json
        """
        scenariotree_path = os.path.abspath(os.path.join(analysis.dataset, "scenariotree.json"))
        if os.path.exists(scenariotree_path):
            with open(scenariotree_path, "r") as file:
                scenariotree_data = json.load(file)
        else:
            raise FileNotFoundError(f"scenariotree.json not found in dataset: {analysis.dataset}")

        return scenariotree_data

    def get_ancestor_node(self, current_node, steps):
        """ returns the ancestor node index of the current node

                :param current_node: index of current node
                :param steps: number of steps to move backwards in the scenariotree
                :return: node index of ancestor (negative if "older" than root node)
                """

        n2r_path = self.node_id_lookup[current_node].node2root_path
        return n2r_path[steps] if steps < len(n2r_path) else len(n2r_path) - (steps + 1)

    def convert_yearly2generic(self, df_input, energy_system):
        """
        Converts and extends the year nodes (e.g., 2025, 2030, 2035) to their
        respective temporal nodes (0, 1, 2, 3, 4, 5) and matches the data.

        :param df_input: Input dataframe with nodes/years/data.
        :param energy_system: Energy system for timestep data access.
        :return: Extended and converted dataframe with columns (node, year, 0).
        """
        # Create mapping from energy_system lists
        df_mapping = pd.DataFrame({
            'time_step': energy_system.set_time_steps_yearly,
            'calendar_year': energy_system.set_temporal_nodes_years
        })

        # Creating the scaffold for all unique nodes and all time steps
        nodes = df_input['node'].unique()
        scaffold = pd.MultiIndex.from_product(
            [nodes, df_mapping['time_step']],
            names=['node', 'time_step']
        ).to_frame(index=False)

        # Merging scaffold with mapping, then with input data
        df_extended = (
            scaffold.merge(df_mapping, on='time_step')
            .merge(
                df_input,
                left_on=['node', 'calendar_year'],
                right_on=['node', 'year'],
                how='left'
            )
        )

        df_final = (
            df_extended.drop(columns=['calendar_year', 'year'])
            .rename(columns={'time_step': 'year'})
            .sort_values(['node', 'year'])
            .reset_index(drop=True)
        )

        return df_final

    def swap_temporal_ID_with_legacy_ID(self, node_ID):
        """
        Swaps new temporal ID's with old year related ID's, used in some data inputs (e.g. existing capacities)

        :param node_ID:
        :return: year in old time_steps_yearly format
                """
        return len(self.node_id_lookup[node_ID].node2root_path)-1

    def add_tree2scenario_dict(self, scenario_dict):
        included_keys = self.extract_scenario_keys()
        sorted_ids = sorted(self.node_id_lookup.keys())

        for key in included_keys:
            element, param, mod_type = key

            # Ensure nested dict structure exists
            if element not in scenario_dict:
                scenario_dict[element] = {}
            if param not in scenario_dict[element]:
                scenario_dict[element][param] = {}

            # Collect values across all nodes
            values = []
            for n_id in sorted_ids:
                val = 1  # Default value
                node = self.node_id_lookup[n_id]
                if node.state is None: #For nodes with no state
                    values.append(str(val))
                    continue
                # Look for this specific key in the current node's state
                for state_item in node.state:
                    if element in state_item:
                        found_val = self.get_nested_val(state_item[element], [param, mod_type])
                        if found_val != 1:
                            val = found_val
                            break
                values.append(str(val))

            # Join values into a comma-separated string
            scenario_dict[element][param][mod_type] = ",".join(values)

    def extract_scenario_keys(self): #TODO: reduced to node_id_op only
        scenario_entries = set()
        for node in self.node_id_lookup.values():
            if node.state is None: continue
            for state_item in node.state:
                for element, params in state_item.items():
                    for param, inner in params.items():
                        if isinstance(inner, dict):
                            for mod_type in inner.keys():
                                scenario_entries.add((element, param, mod_type))
        return scenario_entries

    def write_yearly_variation(self, data_input_object, file_name, df_structure, scenariotree_factors):
        """method that creates a year/temporal node wise output for multi-value per year parameters
        """
        yearly_variation = df_structure #TODO: create this


        parameter_name = file_name + "_yearly_variation"
        setattr(data_input_object, parameter_name, yearly_variation)
        return

    def expand_single_default_value(self):
        """method that creates a year/temporal node wise output for single value parameters
        not in use so far
        """
        return

    @staticmethod
    def get_nested_val(data, path):
        """Helper to navigate nested dicts; returns default 1 if path doesn't exist."""
        for key in path:
            if isinstance(data, dict) and key in data:
                data = data[key]
            else:
                return 1
        return data[0] if isinstance(data, list) else data