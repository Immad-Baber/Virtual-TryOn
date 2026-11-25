from gradio_client import Client, handle_file

print("1. Testing IDM-VTON Space...")
try:
    c = Client("yisol/IDM-VTON")
    print("✅ IDM-VTON Client loaded successfully!")
    endpoints = c.view_api(return_format="dict")["named_endpoints"].keys()
    print("   Endpoints:", list(endpoints))
except Exception as e:
    print("❌ IDM-VTON failed:", e)

print("\n2. Testing CatVTON Space...")
try:
    c2 = Client("zhengchong/CatVTON")
    print("✅ CatVTON Client loaded successfully!")
    endpoints2 = c2.view_api(return_format="dict")["named_endpoints"].keys()
    print("   Endpoints:", list(endpoints2))
except Exception as e:
    print("❌ CatVTON failed:", e)
