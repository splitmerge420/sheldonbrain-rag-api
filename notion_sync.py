"""
Sync Sheldonbrain OS with Pinecone vector store.
Bidirectional: Notion -> Pinecone and Pinecone -> Notion.
"""

from notion_client import Client
from config import NOTION_API_KEY, SHELDONBRAIN_DATABASE_ID
from pinecone_client import upsert_document, query_similar
from datetime import datetime

notion = Client(auth=NOTION_API_KEY)


def fetch_sheldonbrain_entries(limit: int = 100) -> list[dict]:
    """
    Fetch entries from Sheldonbrain OS database.
    """
    response = notion.databases.query(
        database_id=SHELDONBRAIN_DATABASE_ID,
        page_size=limit,
        sorts=[{"property": "Date Discovered", "direction": "descending"}]
    )
    
    entries = []
    for page in response["results"]:
        props = page["properties"]
        
        # Extract key fields
        entry = {
            "id": page["id"],
            "url": page["url"],
            "discovery": get_title(props.get("Discovery", {})),
            "summary": get_rich_text(props.get("Summary", {})),
            "sphere": get_select(props.get("Sphere", {})),
            "sphere_name": get_select(props.get("Sphere Name", {})),
            "category": get_select(props.get("Category", {})),
            "claude_output": get_rich_text(props.get("Council Output (Claude)", {})),
            "grok_output": get_rich_text(props.get("Council Output (Grok)", {})),
            "feast_mode": props.get("Feast Mode", {}).get("checkbox", False)
        }
        entries.append(entry)
    
    return entries


def get_title(prop: dict) -> str:
    """Extract title text from Notion property."""
    if not prop or "title" not in prop:
        return ""
    return "".join([t.get("plain_text", "") for t in prop["title"]])


def get_rich_text(prop: dict) -> str:
    """Extract rich text from Notion property."""
    if not prop or "rich_text" not in prop:
        return ""
    return "".join([t.get("plain_text", "") for t in prop["rich_text"]])


def get_select(prop: dict) -> str:
    """Extract select value from Notion property."""
    if not prop or "select" not in prop or not prop["select"]:
        return ""
    return prop["select"].get("name", "")


def sync_to_pinecone(entries: list[dict], namespace: str = "baseline") -> int:
    """
    Sync Notion entries to Pinecone.
    
    Returns:
        Number of entries synced
    """
    synced = 0
    
    for entry in entries:
        # Build content for embedding
        content = f"""
        Title: {entry['discovery']}
        Sphere: {entry['sphere']} - {entry['sphere_name']}
        Category: {entry['category']}
        Summary: {entry['summary']}
        Claude Analysis: {entry['claude_output']}
        Grok Analysis: {entry['grok_output']}
        """.strip()
        
        # Build metadata
        metadata = {
            "notion_id": entry["id"],
            "notion_url": entry["url"],
            "sphere": entry["sphere"],
            "sphere_name": entry["sphere_name"],
            "category": entry["category"],
            "feast_mode": entry["feast_mode"],
            "source": "sheldonbrain_os"
        }
        
        # Upsert to Pinecone
        upsert_document(content, metadata, namespace)
        synced += 1
    
    print(f"📈 Synced {synced} entries to Pinecone")
    return synced


def full_sync():
    """
    Perform full sync from Sheldonbrain OS to Pinecone.
    """
    print("🔄 Starting full sync...")
    entries = fetch_sheldonbrain_entries(limit=500)
    print(f"📥 Fetched {len(entries)} entries from Sheldonbrain OS")
    synced = sync_to_pinecone(entries)
    print(f"✅ Full sync complete: {synced} entries")
    return synced


if __name__ == "__main__":
    full_sync()
