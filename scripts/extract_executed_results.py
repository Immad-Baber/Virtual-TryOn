import json
import os
import base64
import pandas as pd

os.makedirs("sample_images/executed_results", exist_ok=True)

# 1. Inspect idm_vton_colab (1).ipynb
idm_nb_path = "notebooks/idm_vton_colab (1).ipynb"
with open(idm_nb_path, "r", encoding="utf-8") as f:
    idm_nb = json.load(f)

print("=== EXTRACTING IDM-VTON NOTEBOOK RESULTS ===")
for i, cell in enumerate(idm_nb["cells"]):
    for o in cell.get("outputs", []):
        if "text" in o:
            txt = "".join(o["text"])
            if "IDM-VTON remote inference succeeded" in txt or "CONTROLLED CROSS-ARCHITECTURE" in txt:
                print(f"[Cell {i} Text Output]:\n{txt}\n")
        if "data" in o and "image/png" in o["data"]:
            img_data = o["data"]["image/png"]
            out_img_path = "sample_images/executed_results/idm_vton_benchmark_result.png"
            with open(out_img_path, "wb") as img_f:
                img_f.write(base64.b64decode(img_data))
            print(f" Saved IDM-VTON generated image to: {out_img_path} ({os.path.getsize(out_img_path)/1024:.1f} KB)")

# 2. Inspect catvton_controlled_experiments copy.ipynb
cat_nb_path = "notebooks/catvton_controlled_experiments copy.ipynb"
with open(cat_nb_path, "r", encoding="utf-8") as f:
    cat_nb = json.load(f)

print("\n=== EXTRACTING CATVTON EXPERIMENTS RESULTS ===")
for i, cell in enumerate(cat_nb["cells"]):
    for o in cell.get("outputs", []):
        if "text" in o:
            txt = "".join(o["text"])
            if "Starting Controlled CFG" in txt or "Starting Controlled DDIM" in txt or "Starting Masking" in txt or "MASTER CONTROLLED" in txt:
                print(f"[Cell {i} Text Output]:\n{txt}\n")
        if "data" in o and "image/png" in o["data"]:
            img_data = o["data"]["image/png"]
            out_img_path = f"sample_images/executed_results/catvton_grid_cell_{i}.png"
            with open(out_img_path, "wb") as img_f:
                img_f.write(base64.b64decode(img_data))
            print(f" Saved CatVTON grid image to: {out_img_path} ({os.path.getsize(out_img_path)/1024:.1f} KB)")
