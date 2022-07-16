from lib.parse_3db import parse_3db_file
from lib.export import export_to_gltf

model_path = '../assets/baby.3db'

print(f'Loading model from {model_path}')
with open(model_path, 'rb') as f:
    file_data = f.read()
    model = parse_3db_file(file_data)
    export_to_gltf(model)
