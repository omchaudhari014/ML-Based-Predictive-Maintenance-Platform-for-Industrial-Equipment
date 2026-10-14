import json
with open('frontend/assets/models/induction_motor.glb', 'rb') as f:
    data = f.read()
    
# Find the JSON chunk
import struct
magic = data[0:4]
version = struct.unpack('<I', data[4:8])[0]
length = struct.unpack('<I', data[8:12])[0]
chunk_length = struct.unpack('<I', data[12:16])[0]
chunk_type = data[16:20]
if chunk_type == b'JSON':
    json_data = json.loads(data[20:20+chunk_length])
    for mesh in json_data.get('meshes', []):
        print("Mesh:", mesh.get('name'))
    for node in json_data.get('nodes', []):
        print("Node:", node.get('name'))
