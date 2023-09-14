import pydot
import os
import json
from tree_sitter import Language, Parser
from anytree import Node, RenderTree

class Analyzer:
    def extract_function_calls(self, node, filename):
        if node["type"] == "call":
            for child in node["children"]:
                if child["type"] == "attribute":
                    function_name = None
                    alias_name = None
                    for grandchild in child["children"]:
                        if grandchild["type"] == "identifier":
                            if alias_name is None:
                                alias_name = grandchild["content"]
                            else:
                                function_name = grandchild["content"]
        for child in node.get("children", []):
            self.extract_function_calls(child, filename)
            
    