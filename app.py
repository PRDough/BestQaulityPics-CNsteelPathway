from flask import Flask, Response, render_template, send_from_directory, abort
import os, re, logging, traceback
import zipstream  # pip 包：zipstream-new

app = Flask(__name__)

IMG_DIR = os.path.join(app.static_folder, "PthWPics")
ALLOWED = (".png", ".jpg", ".jpeg", ".gif", ".webp")

app.logger.setLevel(logging.INFO)

def list_images():
    if not os.path.isdir(IMG_DIR):
        app.logger.error("IMG_DIR not found: %s", IMG_DIR)
        return []
    files = [f for f in os.listdir(IMG_DIR) if f.lower().endswith(ALLOWED)]

    def extract_number(filename):
        m = re.search(r'(\d+)', filename)
        return int(m.group(1)) if m else float("inf")

    files_sorted = sorted(files, key=extract_number)
    app.logger.info("list_images -> %d files", len(files_sorted))
    return files_sorted

@app.route("/")
def home():
    imgs = list_images()
    return render_template("index.html", imgs=imgs)

@app.route("/download/<path:filename>")
def download_image(filename):
    if not filename.lower().endswith(ALLOWED):
        abort(404)
    return send_from_directory(IMG_DIR, filename, as_attachment=True)

def read_in_chunks(path, chunk_size=16 * 1024):
    with open(path, "rb") as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            yield chunk

@app.route("/download/all")
def download_all():
    try:
        if not os.path.exists(IMG_DIR):
            app.logger.error("PthWPics not found on server: %s", IMG_DIR)
            return "Error: PthWPics folder not found on server.", 404

        files = list_images()
        if not files:
            app.logger.warning("No images to zip in %s", IMG_DIR)

        # 仅打包不压缩（更快），并允许 Zip64
        z = zipstream.ZipFile(mode="w", compression=zipstream.ZIP_STORED, allowZip64=True)

        for filename in files:
            path = os.path.join(IMG_DIR, filename)
            if os.path.isfile(path):
                app.logger.info("Zipping: %s", filename)
                # ✅ 关键修正：参数名是 iterable
                z.write_iter(arcname=filename, iterable=read_in_chunks(path))
            else:
                app.logger.warning("Skip non-file: %s", path)

        return Response(
            z,
            mimetype="application/zip",
            headers={"Content-Disposition": "attachment; filename=all_PthWPics.zip"},
            direct_passthrough=True,
        )
    except Exception as e:
        app.logger.error("download_all exception: %s", e)
        app.logger.error(traceback.format_exc())
        return "Internal Server Error during zipping.", 500

if __name__ == "__main__":
    app.run(debug=True)
