import os
from tree_sitter import Language, Parser

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

class DirAstCreateClass:
    def __init__(self, target_dir_path, output_yaml_dir):
        self.dir_path = target_dir_path
        self.output_yaml_dir = output_yaml_dir
        os.makedirs(self.output_yaml_dir, exist_ok=True)

    def get_file_content(self, filepath):
        with open(filepath, "r") as f:
            file_content = f.read()
        return file_content

    def get_ast(self, file_content, language):
        parser = Parser()
        parser.set_language(language)
        tree = parser.parse(file_content)
        return tree

    def process_directory(self):
        for root, dirs, files in os.walk(self.dir_path):
            for file in files:
                if file.endswith(".py"):
                    filepath = os.path.join(root, file)
                    file_content = self.get_file_content(filepath)
                    
                    filename = os.path.splitext(file)[0]
                    yaml_filepath = os.path.join(self.output_yaml_dir, f"{filename}.yaml")
                    
                    ast = self.get_ast(file_content, PYTHON_LANGUAGE)
                    self.write_ast_to_yaml(ast, yaml_filepath, file_content)

    def write_ast_to_yaml(self, ast, yaml_filepath, file_content):
        # ASTをYAMLファイルに書き込む処理を追加する必要があります。
        pass

# 使用例
target_dir_path = "/path/to/your/code/directory"
output_yaml_dir = "/path/to/output/yaml/directory"
ast_creator = DirAstCreateClass(target_dir_path, output_yaml_dir)
ast_creator.process_directory()
