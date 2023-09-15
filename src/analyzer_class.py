import pydot
import os
import json
from tree_sitter import Language, Parser
from anytree import Node, RenderTree
from db_class import Db as db

class Analyzer:
    def extract_import_statements(self, data, filename, db_path):
        if isinstance(data, dict):
            for key, value in data.items():
                if key == 'type' and value in ['import_statement', 'import_from_statement']:
                    if value == 'import_from_statement':
                        dotted_names = [child['content'] for child in data['children'] if child['type'] == 'dotted_name']
                        aliased_import = [child for child in data['children'] if child['type'] == 'aliased_import']
                        alias = None
                        if aliased_import:
                            alias_list = [child['content'] for child in aliased_import[0]['children'] if child['type'] == 'identifier']
                            if alias_list:
                                alias = alias_list[0]
                        if aliased_import:
                            imported = [child['content'] for child in aliased_import[0]['children'] if child['type'] == 'dotted_name'][0]
                            db.insert_import_db_values(db_path, filename, dotted_names[0], imported, alias)
                        elif len(dotted_names) > 1:
                            db.insert_import_db_values(db_path, filename, dotted_names[0], dotted_names[1], None)
                    elif value == 'import_statement':
                        if 'aliased_import' in [child['type'] for child in data['children']]:
                            aliased_import = [child for child in data['children'] if child['type'] == 'aliased_import']
                            alias = None
                            if aliased_import:
                                alias_list = [child['content'] for child in aliased_import[0]['children'] if child['type'] == 'identifier']
                                if alias_list:
                                    alias = alias_list[0]
                            imported = [child['content'] for child in aliased_import[0]['children'] if child['type'] == 'dotted_name']
                            if imported:
                                db.insert_import_db_values(db_path, filename, None, imported[0], alias)
                        else:
                            imported = [child['content'] for child in data['children'] if child['type'] == 'dotted_name']
                            if imported:
                                db.insert_import_db_values(db_path, filename, None, imported[0], None)
                else:
                    self.extract_import_statements(value, filename, db_path)
        elif isinstance(data, list):
            for item in data:
                self.extract_import_statements(item, filename, db_path)
    
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
            
    def get_class_name(self, node):
        class_name = None
        for child in node["children"]:
            if child["type"] == "identifier":
                class_name = child["content"]
                break
        return class_name