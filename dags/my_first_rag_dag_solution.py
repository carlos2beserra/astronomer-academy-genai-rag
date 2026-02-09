"""
## Simple RAG DAG to ingest new knowledge data into a vector database

This DAG ingests text data from markdown files, chunks the text, and then ingests 
the chunks into a Weaviate vector database.
"""

from airflow.decorators import dag, task
from airflow.models.baseoperator import chain
from airflow.operators.empty import EmptyOperator
from pendulum import datetime, duration
import os
import logging
import pandas as pd
import weaviate
from weaviate.auth import AuthApiKey

t_log = logging.getLogger("airflow.task")

# Variables used in the DAG
_INGESTION_FOLDERS_LOCAL_PATHS = os.getenv("INGESTION_FOLDERS_LOCAL_PATHS", "/usr/local/airflow/include/data")
_WEAVIATE_HOST = os.getenv("WEAVIATE_HOST", "weaviate")
_WEAVIATE_PORT = int(os.getenv("WEAVIATE_PORT", "8081"))
_WEAVIATE_API_KEY = os.getenv("WEAVIATE_API_KEY", "adminkey")
_WEAVIATE_CLASS_NAME = os.getenv("WEAVIATE_CLASS_NAME", "AirflowDocs")
_OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

_CREATE_CLASS_TASK_ID = "create_class"
_CLASS_ALREADY_EXISTS_TASK_ID = "class_already_exists"


def get_weaviate_client():
    """Get Weaviate client."""
    return weaviate.connect_to_local(
        host=_WEAVIATE_HOST,
        port=_WEAVIATE_PORT,
        auth_credentials=AuthApiKey(_WEAVIATE_API_KEY),
        headers={"X-OpenAI-Api-Key": _OPENAI_API_KEY} if _OPENAI_API_KEY else {},
    )


@dag(
    dag_display_name="📚 Ingest Knowledge Base",
    start_date=datetime(2024, 5, 1),
    schedule="@daily",
    catchup=False,
    max_consecutive_failed_dag_runs=5,
    tags=["RAG"],
    default_args={
        "retries": 3,
        "retry_delay": duration(minutes=5),
        "owner": "AI Task Force",
    },
    doc_md=__doc__,
    description="Ingest knowledge into the vector database for RAG.",
)
def my_first_rag_dag_solution():

    @task.branch(retries=4)
    def check_class(
        class_name: str,
        create_class_task_id: str,
        class_already_exists_task_id: str,
    ):
        """Check if the target collection exists in Weaviate."""
        client = get_weaviate_client()
        try:
            exists = client.collections.exists(class_name)
            if not exists:
                t_log.info(f"Collection {class_name} does not exist yet.")
                return create_class_task_id
            else:
                t_log.info(f"Collection {class_name} already exists.")
                return class_already_exists_task_id
        finally:
            client.close()

    check_class_obj = check_class(
        class_name=_WEAVIATE_CLASS_NAME,
        create_class_task_id=_CREATE_CLASS_TASK_ID,
        class_already_exists_task_id=_CLASS_ALREADY_EXISTS_TASK_ID,
    )

    @task
    def create_class(class_name: str) -> None:
        """Create a collection in Weaviate with text2vec-openai vectorizer."""
        from weaviate.classes.config import Configure, Property, DataType
        
        client = get_weaviate_client()
        try:
            client.collections.create(
                name=class_name,
                vectorizer_config=Configure.Vectorizer.text2vec_openai(),
                properties=[
                    Property(name="folder_path", data_type=DataType.TEXT),
                    Property(name="title", data_type=DataType.TEXT),
                    Property(name="text", data_type=DataType.TEXT),
                    Property(name="full_text", data_type=DataType.TEXT),
                    Property(name="uri", data_type=DataType.TEXT),
                    Property(name="chunk_index", data_type=DataType.INT),
                ],
            )
            t_log.info(f"Created collection {class_name}")
        finally:
            client.close()

    create_class_obj = create_class(class_name=_WEAVIATE_CLASS_NAME)

    class_already_exists = EmptyOperator(task_id=_CLASS_ALREADY_EXISTS_TASK_ID)

    weaviate_ready = EmptyOperator(task_id="weaviate_ready", trigger_rule="none_failed")

    chain(check_class_obj, [create_class_obj, class_already_exists], weaviate_ready)

    @task
    def fetch_ingestion_folders_local_paths(ingestion_folders_local_path):
        """Get all folders in the ingestion path."""
        folders = os.listdir(ingestion_folders_local_path)
        return [
            os.path.join(ingestion_folders_local_path, folder) for folder in folders
        ]

    fetch_ingestion_folders_local_paths_obj = fetch_ingestion_folders_local_paths(
        ingestion_folders_local_path=_INGESTION_FOLDERS_LOCAL_PATHS
    )

    @task(map_index_template="{{ my_custom_map_index }}")
    def extract_document_text(ingestion_folder_local_path):
        """Extract information from markdown files in a folder."""
        files = [
            f for f in os.listdir(ingestion_folder_local_path) if f.endswith(".md")
        ]

        titles = []
        texts = []

        for file in files:
            file_path = os.path.join(ingestion_folder_local_path, file)
            titles.append(file.split(".")[0])

            with open(file_path, "r", encoding="utf-8") as f:
                texts.append(f.read())

        document_df = pd.DataFrame(
            {
                "folder_path": ingestion_folder_local_path,
                "title": titles,
                "text": texts,
            }
        )

        t_log.info(f"Number of records: {document_df.shape[0]}")

        from airflow.operators.python import get_current_context
        context = get_current_context()
        context["my_custom_map_index"] = f"Extracted files from: {ingestion_folder_local_path}."

        return document_df

    extract_document_text_obj = extract_document_text.expand(
        ingestion_folder_local_path=fetch_ingestion_folders_local_paths_obj
    )

    @task(map_index_template="{{ my_custom_map_index }}")
    def chunk_text(df):
        """Chunk the text in the DataFrame."""
        from langchain.text_splitter import RecursiveCharacterTextSplitter
        from langchain.schema import Document

        splitter = RecursiveCharacterTextSplitter()

        df["chunks"] = df["text"].apply(
            lambda x: splitter.split_documents([Document(page_content=x)])
        )

        df = df.explode("chunks", ignore_index=True)
        df.dropna(subset=["chunks"], inplace=True)
        df["text"] = df["chunks"].apply(lambda x: x.page_content)
        df.drop(["chunks"], inplace=True, axis=1)
        df.reset_index(inplace=True, drop=True)

        from airflow.operators.python import get_current_context
        context = get_current_context()
        context["my_custom_map_index"] = f"Chunked files from a df of length: {len(df)}."

        return df

    chunk_text_obj = chunk_text.expand(df=extract_document_text_obj)

    @task(map_index_template="{{ my_custom_map_index }}")
    def ingest_data(df, class_name: str):
        """Ingest data into Weaviate."""
        client = get_weaviate_client()
        try:
            collection = client.collections.get(class_name)
            
            # Prepare objects for batch import
            objects_to_insert = []
            for idx, row in df.iterrows():
                obj = {
                    "folder_path": row.get("folder_path", ""),
                    "title": row.get("title", ""),
                    "text": row.get("text", ""),
                    "full_text": row.get("text", ""),
                    "uri": f"{row.get('folder_path', '')}/{row.get('title', '')}",
                    "chunk_index": int(idx),
                }
                objects_to_insert.append(obj)
            
            # Batch insert
            with collection.batch.dynamic() as batch:
                for obj in objects_to_insert:
                    batch.add_object(properties=obj)
            
            t_log.info(f"Ingested {len(objects_to_insert)} objects into {class_name}")
            
            from airflow.operators.python import get_current_context
            context = get_current_context()
            folder = df["folder_path"].iloc[0] if len(df) > 0 else "unknown"
            context["my_custom_map_index"] = f"Ingested files from: {folder}."
            
        finally:
            client.close()

    ingest_data_obj = ingest_data.partial(class_name=_WEAVIATE_CLASS_NAME).expand(df=chunk_text_obj)

    chain(
        [chunk_text_obj, weaviate_ready],
        ingest_data_obj,
    )


my_first_rag_dag_solution()
