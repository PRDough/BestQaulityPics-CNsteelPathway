from flask import Flask, Response, render_template, send_from_directory, abort
import os, re
import zipstream  # pip 包：zipstream-new

app = Flask(__name__)

IMG_DIR = os.path.join(app.static_folder, "PthWPics")
ALLOWED = (".png", ".jpg", ".jpeg", ".gif", ".webp")

def list_images():
    if not os.path.isdir(IMG_DIR):
        return []
    files = [f for f in os.listdir(IMG_DIR) if f.lower().endswith(ALLOWED)]
    def extract_number(filename):
        m = re.search(r'(\d+)', filename)
        return int(m.group(1)) if m else float("inf")
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

# —— 改造点在这里 —— #
def read_in_chunks(path, chunk_size=64 * 1024):
    """按块读取文件，保证持续向客户端产出数据，避免超时"""
    with open(path, "rb") as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            yield chunk

@app.route("/download/all")
def download_all():
    if not os.path.exists(IMG_DIR):
        return "Error: PthWPics folder not found on server.", 404

    # 仅打包不压缩，速度快且 CPU 占用低；也支持大文件
    z = zipstream.ZipFile(mode="w", compression=zipstream.ZIP_STORED, allowZip64=True)

    for filename in list_images():
        path = os.path.join(IMG_DIR, filename)
        if os.path.isfile(path):
            # ❗用 write_iter，把“读取文件的生成器”交给 zipstream
            z.write_iter(arcname=filename, iterator=read_in_chunks(path))

    # Response 直接返回 zipstream 对象；它会迭代产出小块字节
    return Response(
        z,
        mimetype="application/zip",
        headers={"Content-Disposition": "attachment; filename=all_PthWPics.zip"},
        direct_passthrough=True,  # 让底层尽量直通传输
    )

if __name__ == "__main__":
    app.run(debug=True)
