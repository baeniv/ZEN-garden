"""
This file implements the scenariotree class
reading, holding and processing the scenariotree information for a stochastic model
"""
from anytree import AnyNode, PreOrderIter
import json
import os

class ScenarioTree:
    """
    Class defining a scenariotree
    """
    def __init__(self,analysis):
        self.data = None
        self.root = None
        self.node_id_lookup = None

        self.json_to_anytree(self.get_scenariotree_data(analysis))
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
            state=node_data["state"],
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
