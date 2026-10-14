"""Fetch the primary training dataset: UCI AI4I 2020 Predictive Maintenance.

Reproducible data acquisition (README references this). Downloads the official
UCI zip and extracts ai4i2020.csv into backend/data/. Falls back with a clear
message if the network is unavailable — training then documents the fallback
rather than silently using a smaller file.

The 10,000-row AI4I set is the TRAINING corpus. The 1,000-record limit in the
app applies only to a user's upload/analysis session, never to training (spec §4).
"""
import io
import os
import ssl
import sys
import zipfile
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.normpath(os.path.join(HERE, "..", "data"))
DEST = os.path.join(DATA_DIR, "ai4i2020.csv")

# Official UCI ML Repository, dataset id 601.
URL = "https://archive.ics.uci.edu/static/public/601/ai4i+2020+predictive+maintenance+dataset.zip"

EXPECTED_HEADER = (
    "UDI,Product ID,Type,Air temperature [K],Process temperature [K],"
    "Rotational speed [rpm],Torque [Nm],Tool wear [min],"
    "Machine failure,TWF,HDF,PWF,OSF,RNF"
)


def verify(path):
    with open(path, "r", encoding="utf-8-sig") as f:
        lines = f.read().splitlines()
    header = lines[0].strip()
    rows = len([ln for ln in lines[1:] if ln.strip()])
    ok = header == EXPECTED_HEADER
    print(f"  header ok: {ok}")
    print(f"  data rows: {rows}")
    if not ok:
        print(f"  WARNING header differs.\n   expected: {EXPECTED_HEADER}\n   got:      {header}")
    return ok, rows


def main():
    os.makedirs(DATA_DIR, exist_ok=True)
    print(f"Downloading AI4I 2020 from UCI ...\n  {URL}")
    try:
        ctx = ssl.create_default_context()
        req = urllib.request.Request(URL, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=90, context=ctx) as r:
            blob = r.read()
        zf = zipfile.ZipFile(io.BytesIO(blob))
        members = [n for n in zf.namelist() if n.lower().endswith("ai4i2020.csv")]
        if not members:
            members = [n for n in zf.namelist() if n.lower().endswith(".csv")]
        if not members:
            raise RuntimeError(f"No CSV inside zip; members={zf.namelist()}")
        with zf.open(members[0]) as src:
            content = src.read()
        with open(DEST, "wb") as out:
            out.write(content)
        print(f"Saved -> {DEST}  ({len(content)} bytes)")
        verify(DEST)
        print("OK")
        return 0
    except Exception as exc:  # noqa: BLE001 - report any failure clearly
        print(f"FAILED to download AI4I 2020: {exc!r}", file=sys.stderr)
        print("Network may be unavailable in this environment.", file=sys.stderr)
        print("Fallback: place ai4i2020.csv in backend/data/ manually, or training "
              "will use the bundled 1,000-row sample and DOCUMENT that limitation.",
              file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
