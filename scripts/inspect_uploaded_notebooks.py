import json
import os

def inspect_nb(path):
    print(f"=== INSPECTING: {path} ===")
    if not os.path.exists(path):
        print("File does not exist!")
        return
    with open(path, "r", encoding="utf-8") as f:
        nb = json.load(f)
    print(f"Total cells: {len(nb['cells'])}")
    for idx, cell in enumerate(nb['cells']):
        if cell['cell_type'] == 'code':
            exec_count = cell.get('execution_count')
            outputs = cell.get('outputs', [])
            out_types = [o.get('output_type') for o in outputs]
            text_outs = []
            image_count = 0
            for o in outputs:
                if 'text' in o:
                    text_outs.append(''.join(o['text'])[:160].strip())
                elif 'data' in o:
                    keys = list(o['data'].keys())
                    text_outs.append(f"data keys: {keys}")
                    if 'image/png' in o['data'] or 'image/jpeg' in o['data']:
                        image_count += 1
                    if 'text/plain' in o['data']:
                        text_outs.append(''.join(o['data']['text/plain'])[:120].strip())
            preview = ''.join(cell['source'])[:70].replace('\n', ' ')
            print(f"Cell {idx:02d} [exec={exec_count}]: out={out_types} imgs={image_count} | {preview}")
            for t in text_outs[:3]:
                print(f"    --> {repr(t)}")

print("\n" + "="*70)
inspect_nb("notebooks/idm_vton_colab (1).ipynb")
print("\n" + "="*70)
inspect_nb("notebooks/catvton_controlled_experiments copy.ipynb")
