# -*- mode: python ; coding: utf-8 -*-
import os
from PyInstaller.utils.hooks import collect_data_files, copy_metadata

# Directory di lavoro (cartella del progetto)
# Usiamo il percorso assoluto per aiutare PyInstaller
pathex = [os.path.abspath('.')]

# ---- Raccogli dati e metadati ----
datas = []

# Manteniamo i tuoi file (app.py e la cartella modules)
datas += [('app.py', '.')]
datas += [('modules', 'modules')]

# Lista di pacchetti che spesso richiedono metadati espliciti per la corretta esecuzione
for pkg in ('streamlit', 'plotly', 'pandas', 'kaleido', 'altair', 'importlib_metadata'):
    try:
        # Aggiunge i data files (assets, templates, ecc.)
        datas += collect_data_files(pkg)
    except Exception:
        pass
    try:
        # Aggiunge i metadati (*.dist-info) - ESSENZIALE PER RISOLVERE PackageNotFoundError
        datas += copy_metadata(pkg)
    except Exception:
        pass

# ---- Hidden imports utili (per risolvere ModuleNotFoundError) ----
hidden_imports = [
    'importlib.metadata',
    'importlib_metadata',
    'pkg_resources',
    # Inclusione esplicita di moduli Streamlit interni
    'streamlit',
    'streamlit.version',
    'pandas',
    'plotly',
    'kaleido',
]

# ---- Analysis (Il blocco principale) ----
a = Analysis(
    ['run_desktop.py'],
    pathex=pathex,
    binaries=[],
    datas=datas, # Usiamo la variabile 'datas' creata sopra
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
    console=False, # Modo windowed/desktop
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)