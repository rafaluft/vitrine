# Monta a vitrine pública a partir da vitrine original (endereço no segredo ORIGEM) e diz se mudou desde a última publicação.
import hashlib, os, pathlib, re, time, urllib.request

ORIGEM = os.environ["ORIGEM"].rstrip("/") + "/"
PUBLICO = os.environ.get("PUBLICO", "").rstrip("/") + "/"

def baixar(caminho, base=ORIGEM):
    sep = "&" if "?" in caminho else "?"
    req = urllib.request.Request(f"{base}{caminho}{sep}t={int(time.time())}", headers={"Cache-Control": "no-cache"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()

site = pathlib.Path("site")
(site / "js").mkdir(parents=True, exist_ok=True)

# vitrine pública: a página que só mostra o pacote pronto (publico/), sem o motor do site
html = baixar("publico/index.html").decode()
html = html.replace("../formulario/", "formulario/").replace("../js/", "js/")
(site / "index.html").write_text(html)
import json
pacote = baixar("publico/pacote.json")
(site / "pacote.json").write_bytes(pacote)
(site / "sites").mkdir(exist_ok=True)
for s in json.loads(pacote).get("sites", []):
    (site / s["arquivo"]).write_bytes(baixar("publico/" + s["arquivo"]))
(site / "js" / "dados-cores.js").write_bytes(baixar("js/dados-cores.js"))  # só as cores e as fotos de mármore (aba Cores)

# formulário do cliente (V1): a página, o catálogo e as fotos de cada opção
try:
    (site / "formulario" / "catalogo").mkdir(parents=True, exist_ok=True)
    (site / "formulario" / "index.html").write_bytes(baixar("formulario/index.html"))
    cat = baixar("formulario/catalogo.json")
    (site / "formulario" / "catalogo.json").write_bytes(cat)
    for itens in json.loads(cat)["pecas"].values():
        for it in itens:
            for campo in ("img", "imgOrig"):  # foto da peça (e a treliça nas cores originais)
                if it.get(campo):
                    (site / "formulario" / it[campo]).write_bytes(baixar("formulario/" + it[campo]))
except Exception as e:
    print("sem formulário:", e)

h = hashlib.sha256()
for f in sorted(p for p in site.rglob("*") if p.is_file()):
    h.update(f.relative_to(site).as_posix().encode()); h.update(f.read_bytes())
versao = h.hexdigest()
(site / "versao.txt").write_text(versao)

antes = ""
if PUBLICO != "/":
    try: antes = baixar("versao.txt", PUBLICO).decode().strip()
    except Exception: pass
mudou = "sim" if versao != antes else "nao"
print("mudou:", mudou)
with open(os.environ.get("GITHUB_OUTPUT", "/dev/null"), "a") as o:
    o.write(f"mudou={mudou}\n")
