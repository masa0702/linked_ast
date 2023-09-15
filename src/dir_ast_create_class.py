import os
import yaml
import subprocess
import graphviz
from tree_sitter import Language, Parser
from graphviz import Digraph
from IPython.display import Image, display

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
    def get_file_content(self, filepath):
        with open(filepath, "r") as f:
            file_content = f.read()
        return file_content

    def get_ast(self, file_content, language):
        parser = Parser()
        parser.set_language(language)
        tree = parser.parse(file_content)
        return tree

    def get_node_label(node):
        # ノードのタイプに基づいて適切なラベルを生成する
        if node.type == 'identifier':
            return f"Identifier:{node.text.decode()}"
        elif node.type == 'literal':
            return f"Literal:{node.text.decode()}"
        else:
            return node.type
    
    def generate_dot(self, node, dot):
        # ラベルのエスケープと囲み
        label = self.get_node_label(node).replace('"', r'\"')
        dot.append(f'  {id(node)} [label="{label}"];')

        for child in node.children:
            # リンクのエスケープと囲み
            dot.append(f'  {id(node)} -> {id(child)};')
            self.generate_dot(child, dot)

    def generate_ast_dot(self, node):
        dot = []
        dot.append('digraph AST {')
        self.generate_dot(node, dot)
        dot.append('}')
        return '\n'.join(dot)
    
    def generate_ast_dict_with_terminal(self, node, source_code):
        result = {'type': node.type}
        if node.child_count > 0:
            result['children'] = [self.generate_ast_dict_with_terminal(c, source_code) for c in node.children]
        if node.is_named:
            start_byte = node.start_byte
            end_byte = node.end_byte
            result['content'] = source_code[start_byte:end_byte].decode()
        return result

    def process_directory(self):
        for root, files in os.walk(self.dir_path):
            for file in files:
                if file.endswith(".py"):
                    filepath = os.path.join(root, file)
                    file_content = self.get_file_content(filepath)
                    
                    filename = os.path.splitext(file)[0]
                    yaml_filepath = os.path.join(self.output_yaml_dir, f"{filename}.yaml")
                    
                    ast = self.get_ast(file_content, PYTHON_LANGUAGE)
                    self.write_ast_to_yaml(ast, yaml_filepath, file_content)

    def write_ast_to_yaml(self, ast, yaml_filepath, source_code):
        ast_dict = self.generate_ast_dict_with_terminal(ast.root_node, source_code)
        with open(yaml_filepath, 'w') as file:
            yaml.dump(ast_dict, file)

    def visualize_ast(self, ast, dot_filepath, png_filepath):
        ast_dot = self.generate_ast_dot(ast.root_node)
        with open(dot_filepath, 'w') as file:
            file.write(ast_dot)

        subprocess.run(['dot', '-Tpng', dot_filepath, '-o', png_filepath], check=True)
        # Display the generated image
        display(Image(png_filepath))
        
# 使用例
# target_dir_path = "/path/to/your/code/directory"
# output_yaml_dir = "/path/to/output/yaml/directory"
# ast_creator = DirAstCreateClass()
# ast_creator.process_directory()
