# hmm3docs

Heroes of Might and Magic III mechanics and AI behaviour, reverse engineered from `Heroes3.exe` (GOG Complete). English and Russian.

Site: https://pashapash.github.io/hmm3docs/ (progress table on the home page)

- `en/`, `ru/`: pages, mirrored file names
- `_data/`: tables generated from the game's text tables, numbers only
- `tools/lod.py`: list or dump entries of a `.lod` archive
- `tools/extract_tables.py`: dumped tables to `_data/*.json`
- `tools/ghidra/DecompAll.java`: headless Ghidra script, decompiles every function to one file

Regenerate data from your own install:

    python3 tools/lod.py dump "<game>/Data/H3ab_bmp.lod" /tmp/h3txt
    python3 tools/extract_tables.py /tmp/h3txt _data

No game files are included.
