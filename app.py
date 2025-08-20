from flask import Flask, render_template, send_from_directory, abort, Response
import os, io, zipfile, re

app = Flask(__name__)

IMG_DIR = os.path.join(app.static_folder, "PthWPics")
ALLOWED = (".png", ".jpg", ".jpeg", ".gif", ".webp")

def list_images():
    if not os.path.isdir(IMG_DIR):
        return []
    files = [f for f in os.listdir(IMG_DIR) if f.lower().endswith(ALLOWED)]

    # 提取文件名中的数字，按数字顺序排序
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
    if not filename.lower().endswith(ALLOWED):
        abort(404)
    return send_from_directory(IMG_DIR, filename, as_attachment=True)

@app.route("/download/all")
def download_all():
    imgs = list_images()
    if not imgs:
        abort(404)

    memfile = io.BytesIO()
    with zipfile.ZipFile(memfile, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        for fn in imgs:
            zf.write(os.path.join(IMG_DIR, fn), arcname=fn)

    memfile.seek(0)
    return Response(
        memfile.getvalue(),
        headers={
            "Content-Type": "application/zip",
            "Content-Disposition": 'attachment; filename="PthWPics.zip"',
        },
    )

if __name__ == "__main__":
    app.run(debug=True)
