from pymongo import MongoClient
import json
from bson import ObjectId

# Connect to MongoDB
client = MongoClient('mongodb://localhost:27017/travel_blog')
db = client.get_default_database()

print("="*60)
print("DATABASE CHECK")
print("="*60)

print("\n1. All collections in database:")
collections = db.list_collection_names()
for col in collections:
    count = db[col].count_documents({})
    print(f"   - {col}: {count} documents")

print("\n2. Checking chunker_datas collection:")
chunker_count = db['chunker_datas'].count_documents({})
print(f"   Total documents in chunker_datas: {chunker_count}")

if chunker_count > 0:
    print("\n3. Sample documents in chunker_datas:")
    for doc in db['chunker_datas'].find().limit(3):
        print(f"\n   Document ID: {doc['_id']}")
        print(f"   Blog ID: {doc.get('blog_id', 'N/A')}")
        print(f"   User ID: {doc.get('user_id', 'N/A')}")
        if 'updated_entities' in doc:
            entities = doc['updated_entities']
            print(f"   Entity types: {list(entities.keys())}")
            for entity_type, entity_list in entities.items():
                print(f"     - {entity_type}: {len(entity_list)} items")
                # Check if descriptions exist
                with_desc = 0
                with_score = 0
                for entity_id, entity_data in entity_list.items():
                    if entity_data.get('description'):
                        with_desc += 1
                    if 'score' in entity_data:
                        with_score += 1
                print(f"       * {with_desc} with descriptions")
                print(f"       * {with_score} with scores (should be 0)")
else:
    print("\n   No documents found in chunker_datas!")
    print("\n4. Checking if document exists with specific ID:")
    specific_doc = db['chunker_datas'].find_one({'_id': ObjectId('696df6c39cb01ac5d00d93cc')})
    if specific_doc:
        print(f"   Found document with ID 696df6c39cb01ac5d00d93cc")
    else:
        print(f"   Document with ID 696df6c39cb01ac5d00d93cc not found")

print("\n" + "="*60)
