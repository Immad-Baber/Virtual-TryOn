import os
import shutil
import json
from PIL import Image

ASSETS_DIR = "app_assets"
os.makedirs(f"{ASSETS_DIR}/cfg_sweep", exist_ok=True)
os.makedirs(f"{ASSETS_DIR}/step_sweep", exist_ok=True)
os.makedirs(f"{ASSETS_DIR}/mask_sweep", exist_ok=True)
os.makedirs(f"{ASSETS_DIR}/model_comparison", exist_ok=True)
os.makedirs(f"{ASSETS_DIR}/ethnic_garments", exist_ok=True)
os.makedirs(f"{ASSETS_DIR}/failures", exist_ok=True)
os.makedirs(f"{ASSETS_DIR}/diagrams", exist_ok=True)

# 1. Slice CFG Sweep (catvton_grid_cell_9.png: 1536x512, 4 panels of 384x512)
grid_cfg = Image.open("sample_images/executed_results/catvton_grid_cell_9.png")
cfg_vals = ["1.5", "2.5", "3.5", "5.0"]
w, h = 384, 512
for i, cfg in enumerate(cfg_vals):
    panel = grid_cfg.crop((i * w, 0, (i + 1) * w, h))
    panel.save(f"{ASSETS_DIR}/cfg_sweep/cfg_{cfg}.png")
grid_cfg.save(f"{ASSETS_DIR}/cfg_sweep/cfg_sweep_banner.png")
print("Sliced CFG sweep panels.")

# 2. Slice Step Sweep (catvton_grid_cell_11.png: 1152x512, 3 panels of 384x512)
grid_step = Image.open("sample_images/executed_results/catvton_grid_cell_11.png")
step_vals = ["20", "35", "50"]
for i, step in enumerate(step_vals):
    panel = grid_step.crop((i * w, 0, (i + 1) * w, h))
    panel.save(f"{ASSETS_DIR}/step_sweep/steps_{step}.png")
grid_step.save(f"{ASSETS_DIR}/step_sweep/step_sweep_banner.png")
print("Sliced Step sweep panels.")

# 3. Slice Mask Sweep (catvton_grid_cell_13.png: 1152x512, 3 panels of 384x512)
grid_mask = Image.open("sample_images/executed_results/catvton_grid_cell_13.png")
mask_types = ["geometric", "anatomical", "extended_kurta"]
for i, mtype in enumerate(mask_types):
    panel = grid_mask.crop((i * w, 0, (i + 1) * w, h))
    panel.save(f"{ASSETS_DIR}/mask_sweep/mask_result_{mtype}.png")
grid_mask.save(f"{ASSETS_DIR}/mask_sweep/mask_sweep_banner.png")

# Copy the actual masks
shutil.copyfile("sample_images/mask_comparison/1_geometric_polygon_mask.png", f"{ASSETS_DIR}/mask_sweep/mask_geometric_binary.png")
shutil.copyfile("sample_images/mask_comparison/2_segformer_anatomical_mask.png", f"{ASSETS_DIR}/mask_sweep/mask_anatomical_binary.png")
shutil.copyfile("sample_images/mask_comparison/3_extended_kurta_mask.png", f"{ASSETS_DIR}/mask_sweep/mask_extended_kurta_binary.png")
print("Sliced Mask sweep panels.")

# 4. Model Comparison Assets
shutil.copyfile("sample_images/executed_results/step4_panel1_person.png", f"{ASSETS_DIR}/model_comparison/benchmark_person.png")
shutil.copyfile("sample_images/official/cloth_23255574.jpg", f"{ASSETS_DIR}/model_comparison/benchmark_garment.jpg")
shutil.copyfile("sample_images/executed_results/women_tryon_result.png", f"{ASSETS_DIR}/model_comparison/catvton_result.png")
shutil.copyfile("sample_images/executed_results/idm_vton_benchmark_result.png", f"{ASSETS_DIR}/model_comparison/idm_vton_result.png")
shutil.copyfile("sample_images/executed_results/catvton_vs_idm_vton_comparison.png", f"{ASSETS_DIR}/model_comparison/comparison_banner.png")
print("Organized model comparison assets.")

# 5. Ethnic Garments Assets
shutil.copyfile("sample_images/person/person_male_01.jpg", f"{ASSETS_DIR}/ethnic_garments/person_male_kurta.jpg")
shutil.copyfile("sample_images/garments/pakistani/kurta_men_royal_blue.jpg", f"{ASSETS_DIR}/ethnic_garments/garment_kurta_blue.jpg")
shutil.copyfile("sample_images/person/person_female_01.jpg", f"{ASSETS_DIR}/ethnic_garments/person_female_kameez.jpg")
shutil.copyfile("sample_images/garments/pakistani/kameez_women_maroon_gold.jpg", f"{ASSETS_DIR}/ethnic_garments/garment_kameez_maroon.jpg")
shutil.copyfile("sample_images/executed_results/men_tryon_result.png", f"{ASSETS_DIR}/ethnic_garments/kurta_tryon_result.png")
shutil.copyfile("sample_images/executed_results/women_tryon_result.png", f"{ASSETS_DIR}/ethnic_garments/kameez_tryon_result.png")
shutil.copyfile("sample_images/mask_comparison/mask_comparison_banner.png", f"{ASSETS_DIR}/ethnic_garments/mask_comparison_banner.png")
print("Organized ethnic garments assets.")

# 6. Failure Analysis Assets
# Slice failure banner from copy_cell_3_out_19.png (1168x512)
if os.path.exists("sample_images/extracted_failures/copy_cell_3_out_19.png"):
    fail_img = Image.open("sample_images/extracted_failures/copy_cell_3_out_19.png")
    fail_img.save(f"{ASSETS_DIR}/failures/geometric_boxy_failure_banner.png")
    # Also save individual panel
    fail_panel = fail_img.crop((fail_img.width - 384, 0, fail_img.width, 512))
    fail_panel.save(f"{ASSETS_DIR}/failures/boxy_garment_result.png")

# Also save CFG 5.0 (excessive guidance) and CFG 1.5 (insufficient guidance)
shutil.copyfile(f"{ASSETS_DIR}/cfg_sweep/cfg_5.0.png", f"{ASSETS_DIR}/failures/failure_excessive_cfg.png")
shutil.copyfile(f"{ASSETS_DIR}/cfg_sweep/cfg_1.5.png", f"{ASSETS_DIR}/failures/failure_insufficient_cfg.png")
shutil.copyfile(f"{ASSETS_DIR}/step_sweep/steps_20.png", f"{ASSETS_DIR}/failures/failure_insufficient_steps.png")
print("Organized failure analysis assets.")

print("All app assets successfully prepared in app_assets/!")
