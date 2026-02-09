"""
## Delete a collection in Weaviate

CAUTION: This DAG will delete a specified collection in your Weaviate instance.
Meant to be used during development to reset Weaviate.
Please use it with caution.
"""

from airflow.decorators import dag, task
from airflow.hooks.base import BaseHook
import weaviate
from weaviate.auth import AuthApiKey
import os

# Provider your Weaviate conn_id here.
WEAVIATE_CONN_ID = os.getenv("WEAVIATE_CONN_ID", "weaviate_default")
# Provide the collection name to delete.
WEAVIATE_COLLECTION_TO_DELETE = "MY_COLLECTION_TO_DELETE"


def get_weaviate_client():
    """Get Weaviate client using connection or environment variables."""
    try:
        conn = BaseHook.get_connection(WEAVIATE_CONN_ID)
        host = conn.host or os.getenv("WEAVIATE_HOST", "weaviate")
        port = conn.port or os.getenv("WEAVIATE_PORT", "8081")
        api_key = conn.password or os.getenv("WEAVIATE_API_KEY", "adminkey")
    except Exception:
        host = os.getenv("WEAVIATE_HOST", "weaviate")
        port = os.getenv("WEAVIATE_PORT", "8081")
        api_key = os.getenv("WEAVIATE_API_KEY", "adminkey")
    
    return weaviate.connect_to_local(
        host=host,
        port=int(port),
        auth_credentials=AuthApiKey(api_key)
    )


@dag(
    dag_display_name="🧼 Delete a Collection in Weaviate",
    schedule=None,
    start_date=None,
    catchup=False,
    description="CAUTION! Will delete a collection in Weaviate!",
    tags=["helper"]
)
def clear_weaviate():

    @task(
        task_display_name=f"Delete {WEAVIATE_COLLECTION_TO_DELETE} in Weaviate",
    )
    def delete_weaviate_collection(collection_to_delete: str):
        client = get_weaviate_client()
        try:
            if client.collections.exists(collection_to_delete):
                client.collections.delete(collection_to_delete)
                print(f"Collection '{collection_to_delete}' deleted successfully.")
            else:
                print(f"Collection '{collection_to_delete}' does not exist.")
        finally:
            client.close()

    delete_weaviate_collection(collection_to_delete=WEAVIATE_COLLECTION_TO_DELETE)


clear_weaviate()
