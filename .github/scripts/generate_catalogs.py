import os
import json

def clean_text(slug):
    # Replaces dashes/underscores with spaces and capitalizes each word
    words = slug.replace('-', ' ').replace('_', ' ').split()
    return ' '.join([w.capitalize() for w in words])

# ==========================================
# GENERATE PHOTOS.JSON
# ==========================================
categories = []
if os.path.exists("images") and os.path.isdir("images"):
    categories = [d for d in os.listdir("images") if os.path.isdir(os.path.join("images", d))]

if not categories:
    categories = ["uncategorized"]

photos_data = {
    "categoryOrder": categories,
    "albums": {}
}

image_extensions = ('.jpg', '.jpeg', '.png', '.webp', '.jpg', '.jpeg', '.png', '.webp')

for cat in categories:
    photos_data["albums"][cat] = []
    cat_dir = os.path.join("images", cat)
    if os.path.exists(cat_dir):
        for file in sorted(os.listdir(cat_dir)):
            if file.lower().endswith(image_extensions):
                base_name = os.path.splitext(file)[0]
                photos_data["albums"][cat].append({
                    "path": f"images/{cat}/{file}",
                    "title": clean_text(cat),
                    "caption": clean_text(base_name)
                })

with open("photos.json", "w", encoding="utf-8") as f:
    json.dump(photos_data, f, indent=2)
print("Successfully generated photos.json")


# ==========================================
# GENERATE DOCUMENTS.JSON
# ==========================================
folders = []
if os.path.exists("documents") and os.path.isdir("documents"):
    folders = [d for d in os.listdir("documents") if os.path.isdir(os.path.join("documents", d))]

if not folders:
    folders = ["uncategorized"]

documents_data = {
    "documentOrder": folders,
    "archives": {}
}

doc_extensions = ('.pdf', '.docx', '.xlsx', '.txt')

for fold in folders:
    documents_data["archives"][fold] = []
    fold_dir = os.path.join("documents", fold)
    if os.path.exists(fold_dir):
        for file in sorted(os.listdir(fold_dir)):
            if file.lower().endswith(doc_extensions):
                base_name = os.path.splitext(file)[0]
                ext_upper = os.path.splitext(file)[1].replace('.', '').upper()
                documents_data["archives"][fold].append({
                    "path": f"documents/{fold}/{file}",
                    "title": clean_text(base_name),
                    "type": ext_upper,
                    "label": clean_text(fold)
                })

with open("documents.json", "w", encoding="utf-8") as f:
    json.dump(documents_data, f, indent=2)
print("Successfully generated documents.json")
