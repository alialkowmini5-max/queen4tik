import os, uuid, shutil, subprocess
from pathlib import Path
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import FileResponse, HTMLResponse

app = FastAPI()
WORK = Path("work"); WORK.mkdir(exist_ok=True)

HTML = """
<!doctype html>
<title>itsscale x2</title>
<h1>ffmpeg -itsscale 2 (copy)</h1>
<form action="/process" method="post" enctype="multipart/form-data">
  <input type="file" name="file" accept="video/*" required />
  <button type="submit">Process</button>
</form>
"""

@app.get("/", response_class=HTMLResponse)
def index():
    return HTML

def run(cmd):
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    if p.returncode != 0:
        raise RuntimeError(p.stdout)

@app.post("/process")
def process(file: UploadFile = File(...)):
    uid = uuid.uuid4().hex
    in_path = WORK / f"in_{uid}.mp4"
    out_path = WORK / f"out_{uid}.mp4"
    with open(in_path, "wb") as f:
        shutil.copyfileobj(file.file, f)
    try:
        run(["ffmpeg","-y","-itsscale","2","-i",str(in_path),
             "-c:v","copy","-c:a","copy","-movflags","+faststart",str(out_path)])
        return FileResponse(str(out_path), media_type="video/mp4",
                            headers={"Content-Disposition": 'attachment; filename="output_itsscale2.mp4"'})
    except Exception as e:
        return {"error": str(e)}
    finally:
        try: os.remove(in_path)
        except: pass