from flask import Flask, Response, render_template, send_from_directory, abort
import os, re, zipstream

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
        match = re.search(r"(\d+)", filename)
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
    """流式打包所有图片为 zip 并下载"""
    if not os.path.exists(IMG_DIR):
        return "Error: PthWPics folder not found on server.", 404

    z = zipstream.ZipFile(mode="w", compression=zipstream.ZIP_DEFLATED)

    for filename in list_images():
        file_path = os.path.join(IMG_DIR, filename)
        if os.path.isfile(file_path):
            z.write(file_path, arcname=filename)

    return Response(
        z,
        mimetype="application/zip",
        headers={"Content-Disposition": "attachment; filename=all_PthWPics.zip"}
    )


if __name__ == "__main__":
    app.run(debug=True)
