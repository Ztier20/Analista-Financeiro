"""
Watcher — Monitoramento Automático de Extratos B3
Detecta novos arquivos .xlsx e processa automaticamente
"""

import time
import shutil
import subprocess
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional
import hashlib


PASTA_MONITORADA = Path.home() / "Downloads"
PASTA_RELATORIOS = Path("data/relatorios")
EXTENSOES = {".xlsx", ".xls"}
INTERVALO_SEGUNDOS = 30


def _hash_arquivo(caminho: Path) -> str:
    return hashlib.md5(caminho.read_bytes()).hexdigest()


def _notificar_windows(titulo: str, mensagem: str):
    """Exibe notificação no Windows via PowerShell"""
    try:
        script = (
            f"Add-Type -AssemblyName System.Windows.Forms; "
            f"[System.Windows.Forms.MessageBox]::Show('{mensagem}', '{titulo}')"
        )
        subprocess.Popen(
            ["powershell", "-WindowStyle", "Hidden", "-Command", script],
            creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, "CREATE_NO_WINDOW") else 0
        )
    except Exception:
        pass


def _parece_extrato_b3(caminho: Path) -> bool:
    """Heurística: nome contém 'posicao', 'extrato', 'b3' ou 'carteira'"""
    nome = caminho.stem.lower()
    return any(p in nome for p in ["posicao", "extrato", "b3", "carteira", "posição"])


def _processar_arquivo(caminho: Path):
    """Copia para pasta de relatórios e roda relatorio.py"""
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    destino_dir = PASTA_RELATORIOS / ts
    destino_dir.mkdir(parents=True, exist_ok=True)

    # Copiar extrato
    destino_xlsx = destino_dir / caminho.name
    shutil.copy2(caminho, destino_xlsx)

    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 📄 Novo extrato detectado: {caminho.name}")
    print(f"  → Salvando em {destino_dir}")

    # Rodar relatorio.py
    relatorio_py = Path(__file__).parent.parent / "relatorio.py"
    if relatorio_py.exists():
        print(f"  → Gerando relatório...")
        try:
            resultado = subprocess.run(
                [sys.executable, str(relatorio_py), str(destino_xlsx)],
                capture_output=True, text=True, timeout=120
            )
            log_path = destino_dir / "relatorio.md"
            if resultado.stdout:
                log_path.write_text(resultado.stdout, encoding="utf-8")
                print(f"  → Relatório salvo em {log_path}")

            if resultado.returncode == 0:
                _notificar_windows(
                    "Analista Financeiro",
                    f"Extrato processado!\n{caminho.name}\nRelatório salvo em data/relatorios/{ts}"
                )
            else:
                print(f"  ⚠️  relatorio.py retornou código {resultado.returncode}")
        except subprocess.TimeoutExpired:
            print("  ⚠️  Timeout ao processar relatório (>120s)")
        except Exception as e:
            print(f"  ⚠️  Erro ao rodar relatorio.py: {e}")
    else:
        print(f"  ⚠️  relatorio.py não encontrado em {relatorio_py}")

    return destino_dir


def iniciar_watcher(
    pasta: Optional[Path] = None,
    intervalo: int = INTERVALO_SEGUNDOS
):
    """
    Inicia o loop de monitoramento

    Args:
        pasta: Pasta a monitorar (padrão: ~/Downloads)
        intervalo: Segundos entre verificações
    """
    pasta = pasta or PASTA_MONITORADA
    PASTA_RELATORIOS.mkdir(parents=True, exist_ok=True)

    print(f"👀 Watcher iniciado")
    print(f"   Monitorando: {pasta}")
    print(f"   Intervalo: {intervalo}s")
    print(f"   Relatórios: {PASTA_RELATORIOS.resolve()}")
    print(f"\nPressione Ctrl+C para parar.\n")

    arquivos_vistos: dict[str, str] = {}  # path → hash

    # Snapshot inicial (ignorar arquivos já existentes)
    for arq in pasta.glob("*"):
        if arq.suffix.lower() in EXTENSOES:
            try:
                arquivos_vistos[str(arq)] = _hash_arquivo(arq)
            except Exception:
                pass

    try:
        while True:
            time.sleep(intervalo)

            for arq in pasta.glob("*"):
                if arq.suffix.lower() not in EXTENSOES:
                    continue

                chave = str(arq)
                try:
                    novo_hash = _hash_arquivo(arq)
                except Exception:
                    continue

                # Arquivo novo ou modificado
                if chave not in arquivos_vistos or arquivos_vistos[chave] != novo_hash:
                    arquivos_vistos[chave] = novo_hash
                    if _parece_extrato_b3(arq):
                        _processar_arquivo(arq)
                    else:
                        print(f"[{datetime.now().strftime('%H:%M:%S')}] "
                              f"📁 Novo .xlsx ignorado (não parece extrato B3): {arq.name}")

    except KeyboardInterrupt:
        print("\n\n⏹️  Watcher encerrado.")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Watcher de extratos B3")
    parser.add_argument("--pasta", type=Path, default=None,
                        help="Pasta a monitorar (padrão: ~/Downloads)")
    parser.add_argument("--intervalo", type=int, default=INTERVALO_SEGUNDOS,
                        help="Intervalo em segundos entre verificações")
    args = parser.parse_args()

    iniciar_watcher(pasta=args.pasta, intervalo=args.intervalo)
