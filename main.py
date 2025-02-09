from fastapi import FastAPI, File, UploadFile, HTTPException, Header, Response, Request, Form, Cookie                                           from fastapi.responses import HTMLResponse, RedirectResponse                                                                                    from fastapi.security import HTTPBasic                                                                                                          from pathlib import Path                                                                                                                        import mimetypes                                                                                                                                import logging                                                                                                                                  import os                                                                                                                                       from datetime import datetime, timedelta                                                                                                        import secrets                                                                                                                                  import hashlib                                                                                                                                                                                                                                                                                  app = FastAPI()                                                                                                                                                                                                                                                                                 # Configuration                                                                                                                                 class Config:                                                                                                                                       UPLOAD_DIR = Path("cdn_files")                                                                                                                  LOGS_DIR = Path("logs")                                                                                                                         MAX_FILE_SIZE = 512 * 1024 * 1024  # 512MB                                                                                                      ADMIN_PASSWORD = "ppp000ppp123Za@"                                                                                                              DAILY_UPLOAD_LIMIT = 1024 * 1024 * 1024  # 1GB per day                                                                                          SESSION_DURATION = timedelta(hours=24)  # Session length                                                                                    PUBLIC_IP = "cdn.kaityxd.xyz"                                                                                                                   # Create directories                                                                                                                            Config.UPLOAD_DIR.mkdir(exist_ok=True)                                                                                                          Config.LOGS_DIR.mkdir(exist_ok=True)                                                                                                                                                                                                                                                            # Setup logging                                                                                                                                 logging.basicConfig(                                                                                                                                filename=Config.LOGS_DIR / 'cdn.log',                                                                                                           level=logging.INFO,                                                                                                                             format='%(asctime)s - %(levelname)s - %(message)s'                                                                                          )                                                                                                                                                                                                                                                                                               # Session storage                                                                                                                               active_sessions = {}                                                                                                                                                                                                                                                                            def create_session_token():                                                                                                                         return secrets.token_urlsafe(32)                                                                                                                                                                                                                                                            def is_valid_session(session_token: str) -> bool:                                                                                                   if session_token not in active_sessions:                                                                                                            return False                                                                                                                                session_time = active_sessions[session_token]                                                                                                   if datetime.now() - session_time > Config.SESSION_DURATION:                                                                                         del active_sessions[session_token]                                                                                                              return False                                                                                                                                return True                                                                                                                                                                                                                                                                                 @app.get("/login", response_class=HTMLResponse)                                                                                                 async def login_page(request: Request):                                                                                                             # Check if already logged in                                                                                                                    admin_auth = request.cookies.get("admin_auth")                                                                                                  if admin_auth and is_valid_session(admin_auth):                                                                                                     return RedirectResponse(url="/admin", status_code=303)                                                                                                                                                                                                                                      html_content = """                                                                                                                              <html>                                                                                                                                          <head>                                                                                                                                              <title>Admin Login</title>                                                                                                                      <style>                                                                                                                                             body {                                                                                                                                              font-family: Arial, sans-serif;                                                                                                                 display: flex;                                                                                                                                  justify-content: center;                                                                                                                        align-items: center;                                                                                                                            height: 100vh;                                                                                                                                  margin: 0;                                                                                                                                      background: #f5f5f5;                                                                                                                        }                                                                                                                                               .login-container {                                                                                                                                  background: white;                                                                                                                              padding: 30px;                                                                                                                                  border-radius: 10px;                                                                                                                            box-shadow: 0 0 10px rgba(0,0,0,0.1);                                                                                                           width: 300px;                                                                                                                               }                                                                                                                                               h2 {                                                                                                                                                text-align: center;
                color: #333;
                margin-bottom: 20px;
            }
            .form-group {
                margin-bottom: 15px;
            }
            input[type="password"] {
                width: 100%;
                padding: 10px;
                border: 1px solid #ddd;
                border-radius: 5px;
                box-sizing: border-box;
            }
            button {
                width: 100%;
                padding: 10px;
                background: #4CAF50;
                color: white;
                border: none;
                border-radius: 5px;
                cursor: pointer;
                font-size: 16px;
            }
            button:hover {
                background: #45a049;
            }
            .error {
                color: red;
                text-align: center;
                margin-bottom: 10px;
                display: none;
            }
        </style>
    </head>
    <body>
        <div class="login-container">
            <h2>Admin Login</h2>
            <form action="/login" method="post">
                <div class="form-group">
                    <input type="password" name="password" placeholder="Enter admin password" required>
                </div>
                <div class="error" id="error-message">Invalid password</div>
                <button type="submit">Login</button>
            </form>
        </div>
        <script>
            // Show error message if redirected with error
            if (window.location.search.includes('error=1')) {
                document.getElementById('error-message').style.display = 'block';
            }
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.post("/login")
async def login(password: str = Form(...)):
    if password == Config.ADMIN_PASSWORD:
        session_token = create_session_token()
        active_sessions[session_token] = datetime.now()
        response = RedirectResponse(url="/admin", status_code=303)
        response.set_cookie(
            key="admin_auth",
            value=session_token,
            httponly=True,
            secure=True,  # Only send over HTTPS
            samesite="strict",  # Protect against CSRF
            max_age=int(Config.SESSION_DURATION.total_seconds())
        )
        return response
    return RedirectResponse(url="/login?error=1", status_code=303)

@app.get("/logout")
async def logout(admin_auth: str = Cookie(None)):
    if admin_auth in active_sessions:
        del active_sessions[admin_auth]
    response = RedirectResponse(url="/login", status_code=303)
    response.delete_cookie("admin_auth")
    return response

@app.get("/admin", response_class=HTMLResponse)
async def admin_panel(request: Request):
    admin_auth = request.cookies.get("admin_auth")
    if not admin_auth or not is_valid_session(admin_auth):
        return RedirectResponse(url="/login", status_code=303)

    files = list(Config.UPLOAD_DIR.iterdir())
    total_size = sum(f.stat().st_size for f in files)

    # Rest of your existing admin panel HTML code remains the same
    html_content = """
    <html>
    <head>
        <title>Admin Panel</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                padding: 20px;
                background: #f5f5f5;
            }
            .container {
                max-width: 800px;
                margin: auto;
                background: white;
                padding: 20px;
                border-radius: 10px;
                box-shadow: 0 0 10px rgba(0,0,0,0.1);
            }
            table {
                width: 100%;
                border-collapse: collapse;
            }
            th, td {
                padding: 10px;
                text-align: left;
                border-bottom: 1px solid #ddd;
            }
            .delete-btn {
                background: #ff4444;
                color: white;
                padding: 5px 10px;
                border: none;
                border-radius: 3px;
                cursor: pointer;
            }
            .filename {
                max-width: 200px;
                white-space: nowrap;
                overflow: hidden;
                text-overflow: ellipsis;
            }
            .logout-btn {
                float: right;
                background: #666;
                color: white;
                padding: 5px 15px;
                border: none;
                border-radius: 3px;
                cursor: pointer;
                text-decoration: none;
            }
            .refresh-btn {
                float: right;
                background: #4CAF50;
                color: white;
                padding: 5px 15px;
                border: none;
                border-radius: 3px;
                cursor: pointer;
                text-decoration: none;
                margin-right: 10px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <a href="/logout" class="logout-btn">Logout</a>
            <a href="/admin" class="refresh-btn">Refresh</a>
            <h2>Admin Panel</h2>
            <p>Total Files: """ + str(len(files)) + """</p>
            <p>Total Storage Used: """ + f"{total_size / (1024*1024):.2f}" + """ MB</p>

            <h3>Files</h3>
            <table>
                <tr>
                    <th>Filename</th>
                    <th>Size</th>
                    <th>Last Modified</th>
                    <th>Actions</th>
                </tr>
                """ + "".join(f"""
                <tr>
                    <td class="filename" title="{f.name}">{f.name}</td>
                    <td>{f.stat().st_size / 1024:.1f} KB</td>
                    <td>{datetime.fromtimestamp(f.stat().st_mtime)}</td>
                    <td><button class="delete-btn" onclick="deleteFile('{f.name}')">Delete</button></td>
                </tr>
                """ for f in files) + """
            </table>
        </div>

        <script>
            function deleteFile(name) {
                if (confirm('Delete ' + name + '?')) {
                    fetch('/admin/delete/' + name, {
                        method: 'DELETE'
                    }).then(response => {
                        if (response.ok) {
                            location.reload();
                        } else {
                            alert('Delete failed');
                        }
                    }).catch(error => {
                        alert('Error: ' + error);
                    });
                }
            }
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.delete("/admin/delete/{filename}")
async def delete_file(filename: str, request: Request):
    admin_auth = request.cookies.get("admin_auth")
    if not admin_auth or not is_valid_session(admin_auth):
        raise HTTPException(status_code=403, detail="Unauthorized")

    file_path = Config.UPLOAD_DIR / filename
    if file_path.exists():
        os.remove(file_path)
        logging.info(f"File deleted: {filename}")
        return {"status": "success"}
    raise HTTPException(status_code=404, detail="File not found")


@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        file_size = len(contents)
        file_path = Config.UPLOAD_DIR / file.filename

        if file_size > Config.MAX_FILE_SIZE:
            raise HTTPException(status_code=403, detail="File too large")

        with open(file_path, "wb") as f:
            f.write(contents)

        logging.info(f"File uploaded: {file.filename}")
        return {"url": f"https://{PUBLIC_IP}/cdn/{file.filename}"}
    except Exception as e:
        logging.error(f"Upload error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/cdn/{filename}")
async def get_file(filename: str):
    file_path = Config.UPLOAD_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")

    mime_type, _ = mimetypes.guess_type(file_path)
    if not mime_type:
        mime_type = "application/octet-stream"

    with open(file_path, "rb") as f:
        return Response(f.read(), media_type=mime_type, headers={"Content-Disposition": "inline"})

@app.get("/library", response_class=HTMLResponse)
async def library(
    page: int = 1,
    limit: int = 20,
    sort_by: str = "date",  # 'date', 'size', 'name'
    order: str = "desc"  # 'asc', 'desc'
):
    # Get all files and apply sorting
    files = list(Config.UPLOAD_DIR.iterdir())

    # Sorting logic
    if sort_by == "date":
        files.sort(key=lambda x: x.stat().st_mtime, reverse=(order == "desc"))
    elif sort_by == "size":
        files.sort(key=lambda x: x.stat().st_size, reverse=(order == "desc"))
    elif sort_by == "name":
        files.sort(key=lambda x: x.name.lower(), reverse=(order == "desc"))

    # Pagination
    total_files = len(files)
    total_pages = max(1, (total_files + limit - 1) // limit)
    page = min(max(1, page), total_pages)

    start_idx = (page - 1) * limit
    end_idx = start_idx + limit
    files_page = files[start_idx:end_idx]

    def truncate_filename(filename, max_length=20):
        if len(filename) <= max_length:
            return filename
        return filename[:max_length-3] + "..."

    file_cards = ""
    for file in files_page:
        file_url = f"/cdn/{file.name}"
        file_type, _ = mimetypes.guess_type(file)
        truncated_name = truncate_filename(file.name)
        file_size = file.stat().st_size
        file_date = datetime.fromtimestamp(file.stat().st_mtime).strftime("%Y-%m-%d %H:%M")

        size_str = f"{file_size/1024/1024:.1f} MB" if file_size > 1024*1024 else f"{file_size/1024:.1f} KB"

        if file.suffix.lower() in ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg']:
            file_cards += f'''
                <div class="card">
                    <a href="{file_url}" target="_blank">
                        <img src="{file_url}" alt="{file.name}" loading="lazy">
                    </a>
                    <div class="card-info">
                        <p title="{file.name}">{truncated_name}</p>
                        <span class="file-meta">{size_str} • {file_date}</span>
                    </div>
                </div>'''
        elif file.suffix.lower() in ['.mp4', '.webm', '.ogg', '.mp3', '.wav', '.flac']:
            file_cards += f'''
                <div class="card">
                    <video controls preload="none">
                        <source src="{file_url}" type="{file_type}">
                    </video>
                    <div class="card-info">
                        <p title="{file.name}">{truncated_name}</p>
                        <span class="file-meta">{size_str} • {file_date}</span>
                    </div>
                </div>'''
        else:
            file_cards += f'''
                <div class="card file-card">
                    <a href="{file_url}" target="_blank" title="{file.name}">
                        <div class="file-icon">📄</div>
                        <div class="card-info">
                            <p>{truncated_name}</p>
                            <span class="file-meta">{size_str} • {file_date}</span>
                        </div>
                    </a>
                </div>'''

    html_content = f"""
    <html>
    <head>
        <title>CDN Library</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                text-align: center;
                padding: 20px;
                background: #f5f5f5;
                margin: 0;
            }}
            .container {{
                max-width: 1200px;
                margin: 0 auto;
                padding: 0 20px;
            }}
            .controls {{
                margin-bottom: 20px;
                display: flex;
                justify-content: space-between;
                align-items: center;
                background: white;
                padding: 15px;
                border-radius: 10px;
                box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            }}
            .controls select, .controls input {{
                padding: 8px;
                border: 1px solid #ddd;
                border-radius: 5px;
                margin-right: 10px;
            }}
            .grid {{
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
                gap: 20px;
                margin-bottom: 20px;
            }}
            .card {{
                background: white;
                border-radius: 10px;
                box-shadow: 0 2px 5px rgba(0,0,0,0.1);
                overflow: hidden;
                transition: transform 0.2s;
            }}
            .card:hover {{
                transform: translateY(-5px);
            }}
            .card img, .card video {{
                width: 100%;
                height: 200px;
                object-fit: cover;
            }}
            .card-info {{
                padding: 10px;
            }}
            .card p {{
                margin: 0;
                font-weight: bold;
                color: #333;
            }}
            .file-meta {{
                font-size: 12px;
                color: #666;
            }}
            .file-card {{
                text-align: left;
                padding: 15px;
            }}
            .file-card a {{
                text-decoration: none;
                color: inherit;
                display: flex;
                align-items: center;
            }}
            .file-icon {{
                font-size: 24px;
                margin-right: 10px;
            }}
            .pagination {{
                display: flex;
                justify-content: center;
                align-items: center;
                gap: 10px;
                margin-top: 20px;
            }}
            .pagination a {{
                padding: 8px 12px;
                background: white;
                border-radius: 5px;
                text-decoration: none;
                color: #333;
                box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            }}
            .pagination a.active {{
                background: #4CAF50;
                color: white;
            }}
            .pagination a:hover:not(.active) {{
                background: #f0f0f0;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h2>CDN Library</h2>
            <div class="controls">
                <div>
                    <select id="sort" onchange="updateParams()">
                        <option value="date" {('selected' if sort_by == 'date' else '')}>Sort by Date</option>
                        <option value="size" {('selected' if sort_by == 'size' else '')}>Sort by Size</option>
                        <option value="name" {('selected' if sort_by == 'name' else '')}>Sort by Name</option>
                    </select>
                    <select id="order" onchange="updateParams()">
                        <option value="desc" {('selected' if order == 'desc' else '')}>Descending</option>
                        <option value="asc" {('selected' if order == 'asc' else '')}>Ascending</option>
                    </select>
                    <select id="limit" onchange="updateParams()">
                        <option value="20" {('selected' if limit == 20 else '')}>20 per page</option>
                        <option value="50" {('selected' if limit == 50 else '')}>50 per page</option>
                        <option value="100" {('selected' if limit == 100 else '')}>100 per page</option>
                    </select>
                </div>
                <div>
                    Total Files: {total_files}
                </div>
            </div>

            <div class="grid">
                {file_cards}
            </div>

            <div class="pagination">
                {'''<a href="?page=1&sort_by={0}&order={1}&limit={2}">&laquo; First</a>'''.format(sort_by, order, limit) if page > 1 else ''}
                {'''<a href="?page={0}&sort_by={1}&order={2}&limit={3}">&lsaquo; Previous</a>'''.format(page-1, sort_by, order, limit) if page > 1 else ''}
                {' '.join(f'''<a href="?page={p}&sort_by={sort_by}&order={order}&limit={limit}" class="{'active' if p == page else ''}">{p}</a>''' for p in range(max(1, page-2), min(total_pages+1, page+3)))}
                {'''<a href="?page={0}&sort_by={1}&order={2}&limit={3}">Next &rsaquo;</a>'''.format(page+1, sort_by, order, limit) if page < total_pages else ''}
                {'''<a href="?page={0}&sort_by={1}&order={2}&limit={3}">Last &raquo;</a>'''.format(total_pages, sort_by, order, limit) if page < total_pages else ''}
            </div>
        </div>

        <script>
            function updateParams() {{
                const sortValue = document.getElementById('sort').value;
                const orderValue = document.getElementById('order').value;
                const limitValue = document.getElementById('limit').value;
                window.location.href = '?page=1&sort_by=' + sortValue + '&order=' + orderValue + '&limit=' + limitValue;
            }}

            document.addEventListener('DOMContentLoaded', function() {{
                const images = document.querySelectorAll('img');
                images.forEach(img => {{
                    img.style.opacity = '0';
                    img.onload = function() {{
                        img.style.transition = 'opacity 0.3s';
                        img.style.opacity = '1';
                    }};
                }});
            }});
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.get("/gui", response_class=Response)
async def gui_upload():
    html_content = f"""
    <html>
    <head>
        <title>Upload File to CDN</title>
        <style>
            body {{ font-family: Arial, sans-serif; text-align: center; padding: 20px; background: #f5f5f5; }}
            form {{ background: white; padding: 20px; border-radius: 10px; box-shadow: 0 0 10px rgba(0,0,0,0.1); width: 300px; margin: auto; }}
            button {{ background: #4CAF50; color: white; padding: 10px; border: none; cursor: pointer; }}
            input {{ width: 100%; padding: 10px; margin: 10px 0; }}
        </style>
    </head>
    <body>
        <h2>Upload a File</h2>
        <form action="/upload" method="post" enctype="multipart/form-data">
            <input type="file" name="file" required><br>
            <input type="password" name="admin-password" placeholder="Admin Password (Optional)">
            <button type="submit">Upload</button>
        </form>
    </body>
    </html>
    """
    return Response(content=html_content, media_type="text/html")


@app.delete("/admin/delete/{filename}")
async def delete_file(filename: str, request: Request):
    admin_auth = request.cookies.get("admin_auth")
    if not admin_auth:
        raise HTTPException(status_code=403, detail="Unauthorized")

    file_path = Config.UPLOAD_DIR / filename
    if file_path.exists():
        os.remove(file_path)
        logging.info(f"File deleted: {filename}")
        return {"status": "success"}
    raise HTTPException(status_code=404, detail="File not found")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
