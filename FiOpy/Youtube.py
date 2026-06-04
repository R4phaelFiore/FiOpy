import os
import sys
import subprocess

try:
    import yt_dlp
except ImportError:
    print("\n  Instalando yt-dlp, aguarde...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "yt-dlp", "--quiet"])
    import yt_dlp

try:
    import imageio_ffmpeg
except ImportError:
    print("\n  Instalando ffmpeg, aguarde...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "imageio-ffmpeg", "--quiet"])
    import imageio_ffmpeg

FFMPEG_PATH = imageio_ffmpeg.get_ffmpeg_exe()

def progress_hook(d):
    if d["status"] == "downloading":
        total = d.get("total_bytes") or d.get("total_bytes_estimate", 0)
        done = d.get("downloaded_bytes", 0)
        if total:
            pct = int(done / total * 100)
            bar = ("█" * (pct // 5)).ljust(20)
            print(f"\r  [{bar}] {pct}%", end="", flush=True)
    elif d["status"] == "finished":
        print(f"\r  [{'█' * 20}] 100%", flush=True)

def download_mp3(url, output_folder):
    os.makedirs(output_folder, exist_ok=True)

    def hook(d):
        progress_hook(d)
        if d["status"] == "finished":
            print("  Convertendo para MP3...")

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": os.path.join(output_folder, "%(title)s.%(ext)s"),
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }],
        "ffmpeg_location": FFMPEG_PATH,
        "quiet": True,
        "no_warnings": True,
        "progress_hooks": [hook],
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            return {"success": True, "title": info.get("title", "audio"), "ext": "mp3"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def _converter_para_h264(tmp, output_file):
    """Converte qualquer codec de vídeo para H.264/AAC via ffmpeg."""
    cmd = [
        FFMPEG_PATH, "-y",
        "-i", tmp,
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "18",
        "-c:a", "aac",
        "-b:a", "192k",
        "-movflags", "+faststart",
        output_file
    ]
    return subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)

def _converter_para_h264_sem_audio(tmp, output_file):
    """Converte para H.264 sem faixa de áudio."""
    cmd = [
        FFMPEG_PATH, "-y",
        "-i", tmp,
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "18",
        "-an",
        "-movflags", "+faststart",
        output_file
    ]
    return subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)

def download_mp4(url, output_folder):
    os.makedirs(output_folder, exist_ok=True)

    downloaded_file = [None]

    def hook(d):
        if d["status"] == "downloading":
            total = d.get("total_bytes") or d.get("total_bytes_estimate", 0)
            done = d.get("downloaded_bytes", 0)
            if total:
                pct = int(done / total * 100)
                bar = ("█" * (pct // 5)).ljust(20)
                print(f"\r  [{bar}] {pct}%", end="", flush=True)
        elif d["status"] == "finished":
            downloaded_file[0] = d.get("filename", "")
            print(f"\r  [{'█' * 20}] 100%", flush=True)
            print("  Convertendo para H.264 (compativel com Windows)...")

    ydl_opts = {
        # Prioriza H.264 nativo; se nao tiver, pega o melhor disponivel
        "format": "bestvideo[vcodec^=avc1]+bestaudio/bestvideo+bestaudio/best",
        "outtmpl": os.path.join(output_folder, "%(title)s_TMP.%(ext)s"),
        "merge_output_format": "mp4",
        "ffmpeg_location": FFMPEG_PATH,
        "quiet": True,
        "no_warnings": True,
        "progress_hooks": [hook],
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            title = info.get("title", "video")
            vcodec = info.get("vcodec", "")

        tmp = downloaded_file[0]
        if not tmp or not os.path.exists(tmp):
            for f in os.listdir(output_folder):
                if "_TMP" in f:
                    tmp = os.path.join(output_folder, f)
                    break

        if not tmp or not os.path.exists(tmp):
            return {"success": False, "error": "Arquivo temporário não encontrado."}

        safe_title = "".join(c for c in title if c not in r'\/:*?"<>|').strip()
        output_file = os.path.join(output_folder, f"{safe_title}.mp4")

        # Se o vídeo já é H.264 nativo, só remuta sem recodificar
        if "avc1" in vcodec or "h264" in vcodec.lower():
            cmd = [
                FFMPEG_PATH, "-y",
                "-i", tmp,
                "-c:v", "copy",
                "-c:a", "aac",
                "-movflags", "+faststart",
                output_file
            ]
            result = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        else:
            # Recodifica para H.264 para garantir compatibilidade
            result = _converter_para_h264(tmp, output_file)

        try:
            os.remove(tmp)
        except Exception:
            pass

        if result.returncode != 0:
            erro = result.stderr.decode(errors="ignore")[-300:]
            return {"success": False, "error": f"Erro ffmpeg: {erro}"}

        return {"success": True, "title": title, "ext": "mp4"}

    except Exception as e:
        return {"success": False, "error": str(e)}

def download_mp4_sem_audio(url, output_folder):
    os.makedirs(output_folder, exist_ok=True)

    downloaded_file = [None]

    def hook(d):
        if d["status"] == "downloading":
            total = d.get("total_bytes") or d.get("total_bytes_estimate", 0)
            done = d.get("downloaded_bytes", 0)
            if total:
                pct = int(done / total * 100)
                bar = ("█" * (pct // 5)).ljust(20)
                print(f"\r  [{bar}] {pct}%", end="", flush=True)
        elif d["status"] == "finished":
            downloaded_file[0] = d.get("filename", "")
            print(f"\r  [{'█' * 20}] 100%", flush=True)
            print("  Convertendo para H.264 sem áudio...")

    ydl_opts = {
        "format": "bestvideo[vcodec^=avc1]/bestvideo/best",
        "outtmpl": os.path.join(output_folder, "%(title)s_TMP.%(ext)s"),
        "ffmpeg_location": FFMPEG_PATH,
        "quiet": True,
        "no_warnings": True,
        "progress_hooks": [hook],
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            title = info.get("title", "video")
            vcodec = info.get("vcodec", "")

        tmp = downloaded_file[0]
        if not tmp or not os.path.exists(tmp):
            for f in os.listdir(output_folder):
                if "_TMP" in f:
                    tmp = os.path.join(output_folder, f)
                    break

        if not tmp or not os.path.exists(tmp):
            return {"success": False, "error": "Arquivo temporário não encontrado."}

        safe_title = "".join(c for c in title if c not in r'\/:*?"<>|').strip()
        output_file = os.path.join(output_folder, f"{safe_title}_sem_audio.mp4")

        if "avc1" in vcodec or "h264" in vcodec.lower():
            cmd = [
                FFMPEG_PATH, "-y",
                "-i", tmp,
                "-c:v", "copy",
                "-an",
                "-movflags", "+faststart",
                output_file
            ]
            result = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        else:
            result = _converter_para_h264_sem_audio(tmp, output_file)

        try:
            os.remove(tmp)
        except Exception:
            pass

        if result.returncode != 0:
            erro = result.stderr.decode(errors="ignore")[-300:]
            return {"success": False, "error": f"Erro ffmpeg: {erro}"}

        return {"success": True, "title": title, "ext": "mp4"}

    except Exception as e:
        return {"success": False, "error": str(e)}

def youtubeDownload():
    url = input("\n  COLOQUE A URL: ").strip()

    if not url:
        print("\n  URL NOT FOUND.")
        return

    print("""
  SELECIONE UMA OPCAO:

    [1] MP3
    [2] MP4
    [3] MP4 SEM AUDIO
    """)

    opcao = input("  OPCAO: ").strip()

    if opcao not in ("1", "2", "3"):
        print("\n  OPCAO INVALIDA.")
        return

    formatos = {"1": "MP3 192kbps", "2": "MP4 (H.264)", "3": "MP4 SEM AUDIO (H.264)"}

    pastaPadrao = os.path.join(os.path.expanduser("~"), "Downloads")
    selecionarPasta = input(f"\n  DIRETORIO PADRAO [ENTER PARA UTILIZAR {pastaPadrao}]: ").strip()

    if not selecionarPasta:
        selecionarPasta = pastaPadrao

    print(f"""
        URL    : {url}
        Pasta  : {selecionarPasta}
        Formato: {formatos[opcao]}
    """)

    print("  REALIZANDO DOWNLOAD... \n")

    if opcao == "1":
        resultado = download_mp3(url, selecionarPasta)
    elif opcao == "2":
        resultado = download_mp4(url, selecionarPasta)
    else:
        resultado = download_mp4_sem_audio(url, selecionarPasta)

    if resultado["success"]:
        ext = resultado["ext"]
        titulo = resultado["title"]
        sufixo = "_sem_audio" if opcao == "3" else ""
        print(f"\n  CONCLUIDO: {titulo}{sufixo}.{ext}")
        print(f"  SALVO EM: {selecionarPasta}")
    else:
        print(f"\n  ERRO: {resultado['error']}")

print("""
  ███████╗██╗ ██████╗ ██████╗ ██╗   ██╗
  ██╔════╝██║██╔═══██╗██╔══██╗╚██╗ ██╔╝
  █████╗  ██║██║   ██║██████╔╝ ╚████╔╝
  ██╔══╝  ██║██║   ██║██╔═══╝   ╚██╔╝
  ██║     ██║╚██████╔╝██║        ██║
  ╚═╝     ╚═╝ ╚═════╝ ╚═╝        ╚═╝
  \n  © RaphaelFiore 2024-Present - Version 1.3.0
""")

input("  ENTER PARA INICIAR O SISTEMA... ")
youtubeDownload()