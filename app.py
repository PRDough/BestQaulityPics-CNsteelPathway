from flask import Flask, send_file, render_template, send_from_directory, abort
import os, io, zipfile, re

app = Flask(__name__)

# 图片目录
IMG_DIR = os.path.join(app.static_folder, "PthWPics")
ALLOWED = (".png", ".jpg", ".jpeg", ".gif", ".webp")


def list_images():
    """列出允许的图片，并按文件名中的数字排序"""
    if not os.path.isdir(IMG_DIR):
        return []
    files = [f for f in os.listdir(IMG_DIR) if f.lower().endswith(ALLOWED)]

    def extract_number(filename):
        match = re.search(r'(\d+)', filename)
        return int(match.group(1)) if match else float("inf")

    return sorted(files, key=extract_number)


@app.route("/")
def home():
    imgs = list_images()
    return render_template("index.html", imgs=imgs)


@app.route("/download/<path:filename>")
def download_image(filename):
    """下载单张图片"""
    if not filename.lower().endswith(ALLOWED):
        abort(404)
    return send_from_directory(IMG_DIR, filename, as_attachment=True)


@app.route("/download/all")
def download_all():
    """打包所有图片下载 (带调试输出)"""
    if not os.path.exists(IMG_DIR):
        print("❌ Error: PthWPics folder not found!", flush=True)
        return "Error: PthWPics folder not found on server.", 404

    print(f"✅ Looking into folder: {IMG_DIR}", flush=True)
    try:
        files = os.listdir(IMG_DIR)
        print("📂 Files found:", files, flush=True)
    except Exception as e:
        print("⚠️ os.listdir failed:", e, flush=True)
        return "Error reading directory", 500

    memory_file = io.BytesIO()
    with zipfile.ZipFile(memory_file, "w", zipfile.ZIP_DEFLATED) as zf:
        for filename in sorted(files):
            if filename.lower().endswith(ALLOWED):
                file_path = os.path.join(IMG_DIR, filename)
                if os.path.isfile(file_path):
                    print(f"➕ Adding {filename} to zip", flush=True)
                    zf.write(file_path, arcname=filename)
    memory_file.seek(0)

    return send_file(
        memory_file,
        as_attachment=True,
        download_name="all_PthWPics.zip",
        mimetype="application/zip"
    )


if __name__ == "__main__":
    app.run(debug=True)
