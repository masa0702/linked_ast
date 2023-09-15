import os
import re 
import yaml
from dir_ast_create_class import DirAstCreateClass

target_dir_path = ""
output_png_dir = "/Users/takelab/linked_ast/output/out_png"
output_dot_dir = "/Users/takelab/linked_ast/output/out_dot"
output_yaml_dir = "/Users/takelab/linked_ast/output/out_yaml"

os.makedirs(output_png_dir, exist_ok=True)
os.makedirs(output_dot_dir, exist_ok=True)
os.makedirs(output_yaml_dir, exist_ok=True)

dirast = DirAstCreateClass(target_dir_path, output_yaml_dir)

for root, dirs, files in os.walk(target_dir_path):
    for file in files:
        if file.endswith(".py"):
            filepath = os.path.join(root, file)
            file_content = dirast.get_file_content(filepath)
            
            filename = os.path.splitext(file)[0]
            dot_filepath = os.path.join(output_dot_dir, f"{filename}.dot")
            png_filepath = os.path.join(output_png_dir, f"{filename}.png")
            yaml_filepath = os.path.join(output_yaml_dir, f"{filename}.yaml")
            
            ast = dirast.get_ast(file_content, "python")
            dirast.write_ast_to_yaml(ast, yaml_filepath)