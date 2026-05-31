import os
import subprocess
import sys

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

PREFIX = "$"

informations = {
    "Copyright": "© RaphaelFiore 2024-Present - https://github.com/R4phaelFiore",
    "Description": "Fiopy - YouTube to MP3 Downloader",
    "Version": "1.0.0"
}

listCommands = [
    "Join",      # Iniciar download
    "Exit",      # Sair do sistema
    "Commands",  # Listar comandos
    "Info",      # Informações do sistema
]


def handlerCommand(command, prefix):
    if command.startswith(prefix):
        return command[len(prefix):]

    print(
        f"\nUtilize o comando com o prefixo '{prefix}'..."
        f"\nPara saber os comandos utilize '{prefix}Commands'"
    )
    return None


def download_mp3(url, output_folder):
    os.makedirs(output_folder, exist_ok=True)

    def progress_hook(d):
        if d["status"] == "downloading":
            total = d.get("total_bytes") or d.get("total_bytes_estimate", 0)
            done  = d.get("downloaded_bytes", 0)
            if total:
                pct = int(done / total * 100)
                bar = ("█" * (pct // 5)).ljust(20)
                print(f"\r  [{bar}] {pct}%", end="", flush=True)
        elif d["status"] == "finished":
            print(f"\r  [{'█' * 20}] 100%", flush=True)
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
        "progress_hooks": [progress_hook],
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            return {"success": True, "title": info.get("title", "audio")}
    except Exception as e:
        return {"success": False, "error": str(e)}


def handleJoin():
    print("""
  ============================================
   Bem-vindo ao Fiopy!
   YouTube to MP3 Downloader

   © RaphaelFiore 2024-Present
   https://github.com/R4phaelFiore
   Todos os direitos reservados.
  ============================================
    """)

    url = input("  Cole a URL do video do YouTube: ").strip()

    if not url:
        print("\n  Nenhuma URL informada. Operacao cancelada.")
        return

    pasta_padrao = os.path.join(os.path.expanduser("~"), "Music")
    pasta_input  = input(f"\n  Pasta de destino (Enter para usar {pasta_padrao}): ").strip()
    pasta        = pasta_input if pasta_input else pasta_padrao

    print(f"""
  --------------------------------------------
   URL    : {url}
   Pasta  : {pasta}
   Formato: MP3 192kbps
  --------------------------------------------
    """)
    print("  Baixando...\n")

    result = download_mp3(url, pasta)

    if result["success"]:
        print(f"\n  Concluido : {result['title']}.mp3")
        print(f"  Salvo em  : {pasta}")
    else:
        print(f"\n  Erro: {result['error']}")


def handleCommands():
    print("\n  Comandos disponíveis:")
    for cmd in listCommands:
        print(f"    {PREFIX}{cmd}")


def handleInfo():
    print()
    for key, value in informations.items():
        print(f"  {key}: {value}")


# ── Início ────────────────────────────────────────────────────────────────────

print("""
  ███████╗██╗ ██████╗ ██████╗ ██╗   ██╗
  ██╔════╝██║██╔═══██╗██╔══██╗╚██╗ ██╔╝
  █████╗  ██║██║   ██║██████╔╝ ╚████╔╝ 
  ██╔══╝  ██║██║   ██║██╔═══╝   ╚██╔╝  
  ██║     ██║╚██████╔╝██║        ██║   
  ╚═╝     ╚═╝ ╚═════╝ ╚═╝        ╚═╝
""")

print(f"  Digite {PREFIX}Commands para ver os comandos disponíveis.")

while True:
    userCommand = input(f"\nDigite um comando ({PREFIX}): ")

    command = handlerCommand(userCommand, PREFIX)

    if command is None:
        continue

    if command in listCommands:

        if command == "Join":
            handleJoin()

        elif command == "Exit":
            print("\n  Saindo do Fiopy. Até mais!\n")
            break

        elif command == "Commands":
            handleCommands()

        elif command == "Info":
            handleInfo()

    else:
        print(f"\n  Comando '{command}' não existente no sistema.")
        print(f"  Use {PREFIX}Commands para ver os comandos disponíveis.")
