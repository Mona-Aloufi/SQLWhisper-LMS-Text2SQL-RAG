# test_streamlit_db.py
import streamlit as st
import os
import sys
from typing import Dict, Any

# Add src to path
sys.path.insert(0, os.path.abspath('.'))

# Import your database modules
from src.db import DatabaseUploader, DatabaseConnection, SchemaExtractor, DatabaseConnector
from src.db.utils import validate_sqlite_file, format_schema_for_model

def main():
    st.set_page_config(
        page_title="Database Connection Test",
        page_icon="🔗",
        layout="wide"
    )

    st.title("🔗 Database Connection System Test")
    st.markdown("""
    Test your database connection system with:
    - SQLite file uploads (saved in data folder)
    - External database connections
    - Schema extraction
    - Model-ready schema formatting
    """)

    # Initialize session state
    for key in ["db_connection", "schema_info", "model_schema", "uploaded_db_path", "pending_config"]:
        if key not in st.session_state:
            st.session_state[key] = None

    uploader = DatabaseUploader()
    connector = DatabaseConnector()

    # Tabs for different functionality
    tab1, tab2, tab3, tab4 = st.tabs([
        "SQLite Upload", 
        "External Connection", 
        "Current Status", 
        "Schema Preview"
    ])

    # -------------------
    # Tab 1: SQLite Upload
    # -------------------
    with tab1:
        st.header("SQLite Database Upload")
        
        # Show existing databases
        existing_dbs = uploader.list_uploaded_databases()
        if existing_dbs:
            st.subheader("Existing Databases in Data Folder")
            for db_info in existing_dbs:
                col1, col2, col3 = st.columns([3,1,1])
                with col1: st.write(f"📁 {db_info['name']}")
                with col2: st.write(f"Size: {db_info['size'] / (1024*1024):.2f} MB")
                with col3:
                    if st.button(f"Delete {db_info['name']}", key=f"del_{db_info['name']}"):
                        if uploader.delete_database(db_info['name']):
                            st.experimental_rerun()

        uploaded_file = st.file_uploader(
            "Upload SQLite database file (.db, .sqlite, .sqlite3)",
            type=['db', 'sqlite', 'sqlite3'],
            key="upload_test"
        )

        if uploaded_file:
            file_path = uploader.save_uploaded_file(uploaded_file, uploaded_file.name)
            st.success(f"✅ Uploaded: {uploaded_file.name}")

            if validate_sqlite_file(file_path):
                st.success("✅ Valid SQLite file")
                st.session_state.uploaded_db_path = file_path

                if st.button("Connect to Uploaded Database"):
                    db_conn = DatabaseConnection({'type': 'sqlite', 'path': file_path})
                    if db_conn.connect():
                        st.session_state.db_connection = db_conn
                        st.success("✅ Connected successfully!")
                        
                        # Extract schema
                        extractor = SchemaExtractor(db_conn)
                        schema_info = extractor.extract_schema()
                        st.session_state.schema_info = schema_info
                        
                        # Format for model
                        st.session_state.model_schema = format_schema_for_model(schema_info)
                        st.success(f"✅ Schema extracted: {len(schema_info)} tables")
                    else:
                        st.error("❌ Failed to connect")
            else:
                st.error("❌ Invalid SQLite file")

    # ------------------------
    # Tab 2: External Connection
    # ------------------------
    with tab2:
        st.header("External Database Connection")
        db_type = st.selectbox("Database Type", ["postgresql", "mysql"], key="ext_db_type")

        # Collect DB credentials
        host = st.text_input("Host", "localhost", key=f"{db_type}_host")
        port = st.number_input("Port", value=5432 if db_type=="postgresql" else 3306, key=f"{db_type}_port")
        database = st.text_input("Database Name", key=f"{db_type}_db")
        user = st.text_input("Username", key=f"{db_type}_user")
        password = st.text_input("Password", type="password", key=f"{db_type}_pass")

        test_config = {
            'type': db_type,
            'host': host,
            'port': int(port),
            'database': database,
            'user': user,
            'password': password
        }

        col1, col2 = st.columns(2)
        with col1:
            if st.button("Test Connection", key="test_conn"):
                if connector.test_connection(test_config):
                    st.success("✅ Connection test successful!")
                    st.session_state.pending_config = test_config
                else:
                    st.error("❌ Connection test failed")

        with col2:
            if st.session_state.pending_config and st.button("Connect", key="connect_ext"):
                db_conn = connector.connect_external(st.session_state.pending_config)
                if db_conn:
                    st.session_state.db_connection = db_conn
                    st.success("✅ Connected successfully!")

                    # Extract schema
                    extractor = SchemaExtractor(db_conn)
                    schema_info = extractor.extract_schema()
                    st.session_state.schema_info = schema_info

                    # Format for model
                    st.session_state.model_schema = format_schema_for_model(schema_info)
                    st.success(f"✅ Schema extracted: {len(schema_info)} tables")
                else:
                    st.error("❌ Failed to connect")

    # -----------------------
    # Tab 3: Current Status
    # -----------------------
    with tab3:
        st.header("Current Connection Status")
        conn = st.session_state.db_connection
        if conn:
            st.success(f"✅ Connected to {conn.db_type} database")
            if st.session_state.schema_info:
                st.success(f"✅ Schema loaded: {len(st.session_state.schema_info)} tables")

                with st.expander("Connection Details"):
                    st.write(f"**Type:** {conn.db_type}")
                    if conn.db_type == "sqlite":
                        st.write(f"**Path:** {conn.db_config['path']}")
                    else:
                        st.write(f"**Host:** {conn.db_config['host']}")
                        st.write(f"**Database:** {conn.db_config['database']}")

                if st.button("Test Query", key="sample_query"):
                    try:
                        first_table = list(st.session_state.schema_info.keys())[0]
                        results = conn.execute_query(f"SELECT COUNT(*) FROM {first_table};")
                        st.write(f"Sample query result: {results[0][0]} rows in {first_table}")
                    except Exception as e:
                        st.error(f"Query failed: {e}")
            else:
                st.info("Schema not loaded yet")
        else:
            st.info("No active database connection")

    # -----------------------
    # Tab 4: Schema Preview
    # -----------------------
    with tab4:
        st.header("Schema Preview")
        if st.session_state.model_schema:
            st.success("✅ Schema ready for Text2SQL model")
            with st.expander("Full Schema for Model"):
                st.code(st.session_state.model_schema, language="text")

            if st.session_state.schema_info:
                for table_name, table_info in st.session_state.schema_info.items():
                    with st.expander(f"Table: {table_name}", expanded=False):
                        st.write(f"**Columns ({len(table_info['columns'])}):**")
                        for col in table_info['columns']:
                            nullable = "Nullable" if col.get("nullable", True) else "NOT NULL"
                            st.write(f"- `{col['name']}` ({col['type']}) - {nullable}")

                        if table_info.get('foreign_keys'):
                            st.write(f"**Foreign Keys ({len(table_info['foreign_keys'])}):**")
                            for fk in table_info['foreign_keys']:
                                st.write(f"- {fk}")
        else:
            st.info("Connect to a database to see schema")

if __name__ == "__main__":
    main()
