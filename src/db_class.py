import sqlite3
import os
import yaml

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

        # テーブル作成のSQL文を動的に生成
        create_table_sql = f"CREATE TABLE IF NOT EXISTS my_table ({', '.join(table_elements)})"
        
        cursor.execute(create_table_sql)
        conn.commit()
        conn.close()
        
    # --- import db ---
    def insert_import_db(self, db_path, from_file, import_file, alias):
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("INSERT OR IGNORE INTO my_tabble VAALUES(?, ?, ?)", (from_file, import_file, alias))
        conn.commit()
        conn.close()
        
    def import_db_main(self, directory, db_dir):
        for filename in os.listdir(directory):
            db_name = f"import_{os.path.splittext(filename)[0]}.db"
            db_path = os.path.join(db_dir, db_name)
            self.create_db_import_elements(db_path, ["from_file", "import_file", "alias"])
            with open(os.path.splitext(filename)[0]) as f:
                data = yaml.safe_load(f)
                .extract_imports_statements(data, db_path)
                print(f"complete : {os.path.splitext(filename)[0]:}")
    
    # 
    
    def show_all_dbs_contents(self, db_dir):
        for filename in os.listdir(db_dir):
            if filename.endwith(".db"):
                db_path = os.path.join(db_dir, filename)
                print(f"---{filename}---")
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                cursor.execute("PEAFMA table_info(my_table)")
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
            
    