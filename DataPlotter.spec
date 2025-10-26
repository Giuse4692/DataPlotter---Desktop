# -*- mode: python ; coding: utf-8 -*-
import os
from PyInstaller.utils.hooks import collect_data_files, copy_metadata

# Directory di lavoro (cartella del progetto)
pathex = [os.path.abspath('.')]

# ---- Raccogli dati e metadati ----
datas = []

# Manteniamo i tuoi file (app.py e la cartella modules)
datas += [('app.py', '.')]
datas += [('modules', 'modules')]

# Lista di pacchetti che spesso richiedono metadati espliciti per la corretta esecuzione
for pkg in ('streamlit', 'plotly', 'pandas', 'kaleido', 'altair', 'importlib_metadata', 'toml'):
    try:
        datas += collect_data_files(pkg)
    except Exception:
        pass
    try:
        datas += copy_metadata(pkg)
    except Exception:
        pass

# ---- Hidden imports utili (per risolvere ModuleNotFoundError) ----
hidden_imports = [
    # importlib / pkg tools
    'importlib.metadata',
    'importlib_metadata',
    'pkg_resources',

    # Streamlit - includiamo sia il vecchio che il nuovo path "web.cli"
    'streamlit',
    'streamlit.version',
    'streamlit.cli',
    'streamlit.web.cli',
    'streamlit.web.bootstrap',
    'streamlit.web.server.server',
    'streamlit.runtime.scriptrunner',
    'streamlit.watcher',
    'streamlit.config',
    # moduli usati dal tuo progetto
    'pandas',
    'plotly',
    'kaleido',
]

# ---- Analysis (Il blocco principale) ----
a = Analysis(
    ['run_desktop.py'],
    pathex=pathex,
    binaries=[],
    datas=datas,  # Usiamo la variabile 'datas' creata sopra
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

# ---- PYZ / EXE ----
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='DataPlotter',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # app grafica / windowed
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
