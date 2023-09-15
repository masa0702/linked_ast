import sqlite3
import os
import yaml
from analyzer_class import Analyzer as analyzer

class Db:
    # --- 共通部分 ---
    def remove_duplicate_rows_keep_one(self, db_path):
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("CREATE TABLE my_table_temp AS SELECT DISTINCT * FROM my_table")
        cursor.execute("DROP TABLE my_table")
        cursor.execute("ALTER TABLE my_table_temp RENAME TO my_table")
        conn.commit()
        conn.close()
    
    def create_db_import_elements(self, db_path, table_elements):
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        create_table_sql = f"CREATE TABLE IF NOT EXISTS my_table ({', '.join(table_elements)})"  
        cursor.execute(create_table_sql)
        conn.commit()
        conn.close()
        
    # --- import db ---
    def insert_import_db(self, db_path, from_file, import_file, alias):
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("INSERT OR IGNORE INTO my_table VALUES(?, ?, ?)", (from_file, import_file, alias))
        conn.commit()
        conn.close()
    
    # --- call attribute db ---
    def insert_call_attribute_db(self, import_db, attribute_db):
        conn_import = sqlite3.connect(import_db)
        conn_attribute = sqlite3.connect(attribute_db)
        cursor_import = conn_import.cursor()
        cursor_attribute = conn_attribute.cursor()
        cursor_import.execute("SELECT from_file, import_file, alias FROM my_table")
        import_values = cursor_import.fetchall()
        for value in import_values:
            caller_file = os.path.splitext(os.path.basename(import_db))[0]
            from_file = value[0]
            import_file = value[1]
            if len(value) > 2:
                alias = value[2]
            else:
                alias = None
            func_name = None
            cursor_attribute.execute("INSERT INTO my_table VALUES(?, ?, ?, ?, ?)", (caller_file, from_file, import_file, alias, func_name))
        conn_attribute.commit()
        conn_attribute.close()
        conn_import.close()
        
    # --- definition db ---
    def create_definition_db(self, db_path):
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE IF NOT EXISTS my_table (def_file TEXT, class_name TEXT, func_name TEXT, id INTEGER)")
        conn.commit()
        conn.close()
    
    def insert_definition_db(self, db_path, def_file, class_name, func_name):
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO my_table (def_file, class_name, func_name) VALUES(?, ?, ?)", (def_file, class_name, func_name))
        conn.commit()
        conn.close()
    
    # --- link db ---
    def create_link_db(self, db_path):
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE IF NOT EXISTS my_table (caller_file TEXT, id INTEGER)")
        conn.commit()
        conn.close()
    
    def insert_link_db(self, db_path, caller_file, key_id):
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO my_table (caller_file, key_id) VALUES(?, ?)", (caller_file, key_id))
        conn.commit()
        conn.close()
    
    def get_id_from_def_db(self, db_path, function_name, class_name):
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM my_table WHERE func_name = ? AND class_name = ?", (class_name, function_name))
        id = cursor.fetchone()
        conn.close()
        if id:
            return id[0]
        else:
            return None
        
    # --- db main ---
    def import_attribute_db_main(self, directory, import_dir, attribute_dir):
        import_db_elements = ["from_file", "import_file", "alias"]
        attribute_db_elements = ["caller_file", "from_file", "import_file", "func_name"]
        self.create_db_import_elements(import_dir, import_db_elements)
        self.create_db_import_elements(attribute_dir, attribute_db_elements)
        for filename in os.listdir(directory):
            if filename.endswith(".yaml"):
                import_name = f"import_{os.path.splittext(filename)[0]}.db"
                import_path = os.path.join(import_dir, import_name)
                attribute_db_name = f"attribute_{os.path.splittext(filename)[0]}.db"
                attribute_db_path = os.path.join(attribute_dir, attribute_db_name)
                with open(os.path.splitext(filename)[0]) as f:
                    data = yaml.safe_load(f)
                    analyzer.extract_import_statements(data, import_path)
                    self.insert_call_attribute_db(import_path, attribute_db_path)
                    print(f"complete : {os.path.splitext(filename)[0]}")
        self.remove_duplicate_rows_keep_one(import_dir)
        self.remove_duplicate_rows_keep_one(attribute_dir)
        
    def definition_db_main(self, directory, db_dir):
        for filename in os.listdir(directory):
            if filename.endwith(".yaml"):
                with open(os.path.join(directory, filename)) as f:
                    data = yaml.safe_load(f)
                    definitions = analyzer.extract_function_definitions(data, filename)
                    for definition in definitions:
                        def_file = filename
                        class_name = definition["class_name"]
                        func_name = definition["function_name"]
                        id = definition["id"]
                        self.insert_definition_db_values(db_dir, def_file, class_name, func_name, id)
        self.remove_duplicate_rows_keep_one(db_dir)
    
    def link_db_main(self, directory, db_dir, def_db_path):
        for filename in os.listdir(directory):
            if filename.endwith(".yaml"):
                with open(os.path.join(directory, filename)) as f:
                    data = yaml.safe_load(f)
                    analyzer.extract_function_calls(data, filename, db_dir, def_db_path)
        self.remove_duplicate_rows_keep_one(db_dir)

    # --- use main ---
    def get_caller_functions(self, db_path, caller_file):
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM my_table WHERE caller_file = ?", (caller_file,))
        result = cursor.fetchall()
        conn.close()
        result = [item[0] for item in result]
        return result
    
    def get_function_ast(self, ast_dir_path, db_path, function_id):
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT def_file, func_name FROM my_table WHERE id = ?", (function_id,))
        result = cursor.fetchone()
        conn.close()
        if result is not None:
            def_file, func_name = result
            ast_node = self.load_ast_from_file(ast_dir_path, def_file)
            if ast_node is not None:
                return self.find_function_node(ast_node, func_name)
        return None
    
    # --- show db contents ---        
    def show_all_dbs_contents(self, db_dir):
        for filename in os.listdir(db_dir):
            if filename.endwith(".db"):
                db_path = os.path.join(db_dir, filename)
                print(f"---{filename}---")
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                cursor.execute("PRAGMA table_info(my_table)")
                columns = [column[1] for column in cursor.fetchall()]
                print(columns)
                cursor.execute("SELECT * FROM my_table")
                rows = cursor.fetchall()
                for row in rows:
                    print(row)
                conn.close()
                print()
                
    def show_db_contents(self, db_path):
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table':")
        tables = cursor.fetchall()
        for table in tables:
            table_name = table[0]
            print(f"Table : {table_name}")
            print("--------------------")
            
            cursor.execute(f"SELECT *FROM {table_name}")
            rows = cursor.fetchall()
            column_names = [description[0] for description in cursor.description]
            print("\t".join(column_names))
            
            for row in rows:
                print("\t".join(str(col) for col in row))
            print()
            conn.close()
            
    