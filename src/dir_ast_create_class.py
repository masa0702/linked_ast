# This class create AST for all code of directory
import os

class DirAstCreateClass:
    def __init__(self, target_dir_path, output_yaml_dir):
        self.dir_path = target_dir_path
        self.output_yaml_dir = output_yaml_dir
        os.makedirs(self.output_yaml_dir, exist_ok=True)
        
        for root, dirs, files in os.walk(self.dir_path):
            for file in files:
                if file.endswith(".py"):
                    filepath = os.path.join(root, file)
                    file_content = get_file_content(filepath)
                    
                    filename = os.path.splitext(file)[0]
                    yaml_filepath = os.path.join(self.output_yaml_dir, f"{filename}.yaml")
                    
                    ast = get_ast(file_content)
                    write_ast_to_yaml(ast, yaml_filepath, file_content)
