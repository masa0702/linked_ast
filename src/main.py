import os
import re 
import yaml
from tree_sitter import Language, Parser
from analyzer_class import Analyzer
from dir_ast_create_class import DirAstCreateClass
from db_class import Db

# パーサーのセットアップ
Language.build_library(
    "build/my-languages.so",
    [
        "vendor/tree-sitter-python",
        "vendor/tree-sitter-javascript",
        "vendor/tree-sitter-go",
    ]
)
GO_LANGUAGE = Language("build/my-languages.so", "go")
JS_LANGUAGE = Language("build/my-languages.so", "javascript")
PYTHON_LANGUAGE = Language("build/my-languages.so", "python")

target_dir_path = "input"
output_png_dir = "output/out_png"
output_dot_dir = "output/out_dot"
output_yaml_dir = "output/out_yaml"
linked_yaml_dir = "output/linked_yaml"

os.makedirs(output_png_dir, exist_ok=True)
os.makedirs(output_dot_dir, exist_ok=True)
os.makedirs(output_yaml_dir, exist_ok=True)

analyzer = Analyzer()
dirast = DirAstCreateClass(PYTHON_LANGUAGE)
db = Db()
for root, dirs, files in os.walk(target_dir_path):
    for file in files:
        if file.endswith(".py"):
            filepath = os.path.join(root, file)
            file_content = dirast.get_file_content(filepath)
            
            filename = os.path.splitext(file)[0]
            dot_filepath = os.path.join(output_dot_dir, f"{filename}.dot")
            png_filepath = os.path.join(output_png_dir, f"{filename}.png")
            yaml_filepath = os.path.join(output_yaml_dir, f"{filename}.yaml")         
            ast = dirast.get_ast(file_content)
            dirast.write_ast_to_yaml(ast, yaml_filepath, file_content)
            dirast.visualize_ast(ast, dot_filepath, png_filepath)
            
import_db_path = "/Users/takelab/linked_ast/save_db/import_db"
attribute_db_path = "/Users/takelab/linked_ast/save_db/attribute_db"
definition_db_path = "/Users/takelab/linked_ast/save_db/definition.db"
link_db_path = "/Users/takelab/linked_ast/save_db/link.db"
link_dot_path = "/Users/takelab/linked_ast/output/link.dot"

db.import_attribute_db_main(output_yaml_dir, import_db_path, attribute_db_path)
db.definition_db_main(output_yaml_dir, definition_db_path)
db.link_db_main(output_yaml_dir, link_db_path, definition_db_path)

for file in os.listdir(output_yaml_dir):
    caller_file = os.path.join(output_yaml_dir, file)
    print(caller_file)
    get_id = db.get_caller_functions(link_db_path, caller_file)
    function_id = get_id[1]
    get_ast = db.get_function_ast(output_yaml_dir, definition_db_path, function_id)
    copyed_ast_subtree = analyzer.copy_ast_subtree(get_ast)
    convert_copied_ast_subtree = analyzer.convert_node_to_yaml(copyed_ast_subtree)
    subtree = analyzer.add_copied_subtree_to_ast(file, convert_copied_ast_subtree)
    linked_ast = analyzer.save_ast_to_yaml(subtree, file, linked_yaml_dir)
    analyzer.convert_yaml_to_dot(linked_ast, link_dot_path)
    