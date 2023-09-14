import pydot
import os
import json
from tree_sitter import Language, Parser
from anytree import Node, RenderTree
from db_class import Db as db

class Analyzer:
    def extract_import_statements(self, data, db_path):
        if isinstance(data, dict):
            for key, value in data.items():
                if key == "type" and value in ["import_statement", "import_from_statement"]:
                    if value == "import_from_statement":
                        dotted_names = [child["content"] for child in data["children"] if child["type"] == "dotted_name"]
                        aliased_import = [child for child in data["children"] if child["type"] == "aliased_import"]
                        if aliased_import:
                            alias = [child["content"] for child in aliased_import[0]["children"] if child["type"] == "identifier"][0]
                            imported = [child["content"] for child in aliased_import[0]["children"] if child["type"] == "dotted_name"][0]
                            db.remove_duplicate_rows_keep_one(db_path)
                        elif len(dotted_names) > 1:
                            db.insert_import_db(db_path, dotted_names[0], dotted_names[1], None)
                            db.remove_duplicate_rows_keep_one(db_path)
                    elif value == "import_statement":
                        if "aliased_import" in [child["type"] for child in data["children"]]:
                            aliased_import = [child for child in data["children"] if child["type"] == "aliased_import"]
                            if aliased_import:
                                alias = [child["content"] for child in aliased_import[0]["children"] if child["type"] == "identifier"]
                                imported = [child["content"] for child in aliased_import[0]["children"] if child["type"] == "dotted_name"]
                                if alias and imported:
                                    db.insert_import_db(db_path, None, imported[0], alias[0])
                                    db.remove_duplicate_rows_keep_one(db_path)
                        else:
                            imported = [child["content"] for child in data["children"] if child["type"] == "dotted_name"]
                            if imported:
                                db.insert_import_db(db_path, None, imported[0], None)
                                db.remove_duplicate_rows_keep_one(db_path)
                else:
                    self.extract_import_statements(value, db_path)
        elif isinstance(data, list):
            for item in data:
                self.extract_import_statements(item, db_path)
    
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
            
    