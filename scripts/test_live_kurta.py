import time
from gradio_client import Client, handle_file
from PIL import Image

p_path = "official_catvton_repo/resource/demo/example/person/men/model_5.png"
c_path = "sample_images/garments/pakistani/kurta_men_royal_blue.jpg"

print("Invoking live IDM-VTON space on Hugging Face ZeroGPU with real files...")
t0 = time.time()
client = Client("yisol/IDM-VTON")
result = client.predict(
    dict={
        "background": handle_file(p_path),
        "layers": [],
        "composite": handle_file(p_path)
    },
    garm_img=handle_file(c_path),
    garment_des="men royal blue traditional long kurta",
    is_checked=True,
    is_checked_crop=False,
    denoise_steps=30,
    seed=42,
    api_name="/tryon"
)
lat = time.time() - t0
print(f"✅ Real Live Try-On Finished in {lat:.2f}s!")
print(f"Output image path: {result[0]}")
img = Image.open(result[0])
img.save("sample_images/executed_results/live_kurta_tryon_result.png")
print("Saved real try-on result of the black/blue kurta to sample_images/executed_results/live_kurta_tryon_result.png!")
