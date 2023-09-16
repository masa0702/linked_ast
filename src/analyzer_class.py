import pydot
import os
import json
import yaml
import graphviz
from tree_sitter import Language, Parser
from graphviz import Digraph
from anytree import Node, RenderTree

class Analyzer:
    def __init__(self):
        self.new_file_path = None
        
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
            if filename.endswith(".yaml") and filename == def_file:
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
        function_name = self.get_function_name(copied_subtree)
        for call_node in call_nodes:
            attribute_node = self.find_attirbute_node(call_node)
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
    
    def find_all_call_nodes(self, ast_data):
        call_nodes = []
        if isinstance(ast_data, dict):
            if ast_data.get("type") == "call":
                call_nodes.append(ast_data)
            if "children" in ast_data:
                for child_data in ast_data["children"]:
                    call_nodes.extend(self.find_all_call_nodes(child_data))
        elif isinstance(ast_data, list):
            for child_data in ast_data:
                call_nodes.extend(self.find_all_call_nodes(child_data))
        return call_nodes
    
    def find_identifier_nodes(self, ast_node):
        identifier_nodes = []
        def traverse(node):
            if isinstance(node, dict) and node.get("type") == "identifier":
                identifier_nodes.append(node)
            if isinstance(node, dict) and "children" in node:
                for child in node["children"]:
                    traverse(child)
            if isinstance(node, list):
                for child in node:
                    traverse(child)
        traverse(ast_node)
        return identifier_nodes
    
    def save_ast_to_yaml(self, ast, original_file_path, save_dir):
        original_file_name = os.path.basename(original_file_path)
        new_file_name = f"linked_{original_file_name}"
        self.new_file_path = os.path.join(save_dir, new_file_name)
        yaml_ast = self.convert_dict_to_yaml(ast)
        print(yaml_ast)
        with open(self.new_file_path, "w") as file:
            file.write(yaml_ast)
    
    def convert_dict_to_yaml(self, data):
        def remove_private_attributes(data):
            if isinstance(data, dict):
                return {
                    key: remove_private_attributes(value)
                    for key, value in data.items()
                    if not key.startswith('_')
                }
            elif isinstance(data, list):
                return [
                    remove_private_attributes(item)
                    for item in data
                ]
            else:
                return data

        cleaned_data = remove_private_attributes(data)
        yaml_data = yaml.dump(cleaned_data)
        return yaml_data
    
    def find_node_by_type(self, ast_data, node_type):
        if isinstance(ast_data, dict) and ast_data.get("type") == node_type:
            return ast_data
        if isinstance(ast_data, dict) and "children" in ast_data:
            for child in ast_data["children"]:
                result = self.find_node_by_type(child, node_type)
                if result is not None:
                    return result
        if isinstance(ast_data, list):
            for item in ast_data:
                result = self.find_node_by_type(item, node_type)
                if result is not None:
                    return result
        return None
    
    def find_attirbute_node(self, ast_data):
        return self.find_node_by_type(ast_data, "attribute")
    
    def convert_yaml_to_dot(self, dot_file):
        with open(self.new_file_path, 'r') as f:
            data = yaml.safe_load(f)
        dot = graphviz.Digraph()
        def traverse(node, parent_id=None):
            node_id = str(id(node))  # ノードオブジェクトのIDを使用
            if isinstance(node, dict):
                if node.get("type") == "identifier" and node.get("content") is not None:
                    label = f"identifier: {node['content']}"
                else:
                    label = node.get("type", "")
                dot.node(node_id, label=label)
                if parent_id is not None:
                    dot.edge(parent_id, node_id)
                for key, value in node.items():
                    if isinstance(value, (dict, list)):
                        traverse(value, parent_id=node_id)
            elif isinstance(node, list):
                for item in node:
                    traverse(item, parent_id=parent_id)
        traverse(data)
        dot.render(dot_file, format='png')