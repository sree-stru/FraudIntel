import re

with open('d:/FraudIntel/backend/agent/tools/mongodb_tools.py', 'r', encoding='utf-8') as f:
    code = f.read()

# 1. Imports
code = code.replace('import pymongo\n', '')
code = code.replace('from agent.config import settings', 'from agent.config import settings\nfrom agent.database import get_database')

# 2. Globals
code = re.sub(r'_client: pymongo.MongoClient = pymongo.MongoClient\(settings\.mongodb_uri\)\n_db = _client\[settings\.mongodb_database\]\n_DB_NAME = settings\.mongodb_database\n', '_DB_NAME = settings.mongodb_database\n', code)

# 3. Replacements
code = code.replace('pymongo.DESCENDING', '-1')

code = code.replace('_db["investigations"].update_one', 'await get_database()["investigations"].update_one')
code = code.replace('_db["alerts"].update_one', 'await get_database()["alerts"].update_one')

code = code.replace('_db["customers"].find_one', 'await get_database()["customers"].find_one')
code = code.replace('_db["alerts"].find_one', 'await get_database()["alerts"].find_one')

# transactions find
code = code.replace('_db["transactions"]', 'get_database()["transactions"]')
code = code.replace('.limit(limit)\n        )', '.limit(limit)\n            .to_list(length=None)\n        )')
# Wait, for await on cursor we need await in front of get_database()
code = code.replace('get_database()["transactions"]\n            .find', 'await get_database()["transactions"]\n            .find')

# Other cursors
code = code.replace('cursor = _db["investigations"].find(query, projection)', 'cursor = await get_database()["investigations"].find(query, projection).to_list(length=None)')
code = code.replace('cursor = _db["entity_relationships"].find(query)', 'cursor = await get_database()["entity_relationships"].find(query).to_list(length=None)')
code = code.replace('cursor = _db["alerts"].find({"status": "new"})', 'cursor = await get_database()["alerts"].find({"status": "new"}).to_list(length=None)')
code = code.replace('cursor = _db["investigations"].find({"analyst_feedback": {"$exists": True, "$not": {"$size": 0}}}).limit(100)', 'cursor = await get_database()["investigations"].find({"analyst_feedback": {"$exists": True, "$not": {"$size": 0}}}).limit(100).to_list(length=None)')

# Cursors with aggregate
code = code.replace('_db["entity_relationships"].aggregate(pipeline)', 'await get_database()["entity_relationships"].aggregate(pipeline).to_list(length=None)')
code = code.replace('_db["fraud_patterns"].aggregate(pipeline)', 'await get_database()["fraud_patterns"].aggregate(pipeline).to_list(length=None)')


with open('d:/FraudIntel/backend/agent/tools/mongodb_tools.py', 'w', encoding='utf-8') as f:
    f.write(code)

print('Refactored mongodb_tools.py!')
