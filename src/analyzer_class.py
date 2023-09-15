import pydot
import os
import json
import yaml
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
    
    def extract_function_calls(self, node, file_name, db_path, def_db_path):
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
                    if function_name and alias_name:
                        id = self.get_id_from_def_db(db_path, function_name, alias_name)
                        db.insert_link_db(db_path, file_name, id)
        for child in node.get("children", []):
            self.extract_function_calls(child, file_name, None)
    
    def extract_function_definitions(self, node, filename, class_name=None):
        definitions = []
        if node["type"] == "function_definition":
            for child in node["children"]:
                if child["type"] == "identifier":
                    function_name = child["content"]
                    definition = {
                        "class_name": class_name,
                        "function_name": function_name,
                        "id": None
                    }
                    definitions.append(definition)
        for child in node.get("children", []):
            if child["type"] == "class_definition":
                class_name = self.get_class_name(child)
            definitions.extend(self.extract_function_definitions(child, filename, class_name))
        return definitions
    
    def get_class_name(self, node):
        class_name = None
        for child in node["children"]:
            if child["type"] == "identifier":
                class_name = child["content"]
                break
        return class_name
    
    # --- use main ---
    def load_ast_from_file(self, directory, def_file):
        for filename in os.listdir(directory):
            if filename.endwith(".yaml") and filename == def_file:
                file_path = os.path.join(directory, filename)
                with open(file_path)as f:
                    ast_data = yaml.safe_load(f)
                    ast_node = self.build_ast_tree(ast_data)
                    return ast_node
        return None
    
    def find_function_ast(self, ast_node, func_name):
        if isinstance(ast_node, Node):
            if ast_node.name == "function_definition" and ast_node.children[1].content == func_name:
                return ast_node
            else:
                for child in ast_node.children:
                    result = self.find_function_ast(child, func_name)
                    if result is not None:
                        return result
        return None
    
    def build_ast_tree(self, ast_data):
        if isinstance(ast_data, dict):
            node_type = ast_data.get("type")
            node_content = ast_data.get("content")
            node = Node(node_type, content=node_content)
            if "children" in ast_data:
                for child_data in ast_data["children"]:
                    child_node = self.build_ast_tree(child_data)
                    child_node.parent = node
            return node
        elif isinstance(ast_data, list):
            parent_node = Node("parent_node")
            for child_data in ast_data:
                child_node = self.build_ast_tree(child_data)
                child_node.parent = parent_node
            return parent_node
        else:
            return Node(ast_data)
        
    def convert_ast_to_yaml(self, ast_node):
        json_data = json.loads(ast_node)
        yaml_data = yaml.dump(json_data)
        return yaml_data
    
    def convert_node_to_yaml(self, node):
        if isinstance(node, Node):
            data = {
                "type": node.name,
                "content": node.content,
                "children": []
            }
            for child in node.children:
                child_data = self.convert_node_to_yaml(child)
                if child_data is not None:
                    data["children"].append(child_data)
            return data
        else:
            return None
        
    def format_yaml_ast(self, yaml_ast):
        def remove_null_values(data):
            if isinstance(data, dict):
                return{
                    key: remove_null_values(value)
                    for key, value in data.items()
                    if value is not None
                }
            elif isinstance(data, list):
                return{
                    remove_null_values(value)
                    for value in data
                    if value is not None
                }
            else:
                return data
        formatted_ast = remove_null_values(yaml_ast)
        return yaml.dump(formatted_ast)
    
    def copy_ast_subtree(self, ast_node):
        if isinstance(ast_node, Node):
            new_node = Node(ast_node.name, content=ast_node.content)
            for child in ast_node.children:
                new_child = self.copy_ast_subtree(child)
                new_child.parent = new_node
            return new_node
        else:
            return Node(ast_node)
        
    def add_copied_subtree_to_ast(self, origin_ast_path, copied_subtree):
        with open(origin_ast_path, "r") as file:
            original_ast_data = yaml.safe_load(file)
        call_nodes = self.find_all_call_nodes(original_ast_data)
        function_name = self.get_functiton_name(copied_subtree)
        for call_node in call_nodes:
            attribute_node = self.find_attibute_node(call_node)
            if attribute_node is not None:
                identifiers = self.find_identifier_nodes(attribute_node)
                if len(identifiers) > 0:
                    right_identifier = identifiers[-1]
                    if right_identifier.get("content") == function_name:
                        parent_node = right_identifier.get("parent")
                        if parent_node is not None:
                            parent_node["children"].append(copied_subtree)
                        else:
                            attribute_node["children"].append(copied_subtree)
                        break
        return original_ast_data
    
    def get_function_name(self, function_node):
        function_def_content = function_node["content"]
        if function_def_content.startswith("def "):
            return function_def_content[4:].split("(")[0]
        return None
    
    