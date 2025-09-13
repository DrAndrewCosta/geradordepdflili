
# LILI – Ultrassom PDF Multigrupos (Deploy Streamlit)
# Execução local: streamlit run streamlit_app.py

import streamlit as st
from PIL import Image
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from datetime import datetime
import io, zipfile, os

# ====== Layout engine ======
def mm2pt(v): 
    return v * mm

def compute_grid(page_w, page_h, rows, cols, margin_mm, gutter_mm, header_mm, footer_mm):
    M = mm2pt(margin_mm)
    G = mm2pt(gutter_mm)
    H = mm2pt(header_mm)
    F = mm2pt(footer_mm)
    avail_w = page_w - 2*M
    avail_h = page_h - 2*M - (H if H>0 else 0) - (F if F>0 else 0)
    cell_w = (avail_w - (cols-1)*G) / cols
    cell_h = (avail_h - (rows-1)*G) / rows
    boxes = []
    for r in range(rows):
        for c in range(cols):
            x = M + c*(cell_w + G)
            y_top = page_h - M - (H if H>0 else 0)
            y = y_top - (r+1)*cell_h - r*G
            boxes.append((x, y, cell_w, cell_h))
    return boxes

def draw_header_footer(c, page_w, page_h, margin_mm, header_mm, footer_mm, title, show_header, show_footer, page_idx, page_total):
    if show_header and header_mm > 0:
        c.setFont("Helvetica-Bold", 12)
        c.drawCentredString(page_w/2, page_h - mm2pt(margin_mm) - 0.6*mm2pt(header_mm), title or "Relatório de Imagens de Ultrassom")
        c.setLineWidth(0.5)
        c.line(mm2pt(margin_mm), page_h - mm2pt(margin_mm) - mm2pt(header_mm),
               page_w - mm2pt(margin_mm), page_h - mm2pt(margin_mm) - mm2pt(header_mm))
    if show_footer and footer_mm > 0:
        c.setFont("Helvetica", 9)
        c.drawCentredString(page_w/2, mm2pt(margin_mm)/2, f"Página {page_idx} de {page_total} — Gerado em {datetime.now().strftime('%d/%m/%Y %H:%M')}")

def paste_image_contain(c, pil_image, box, caption_text=None, caption_pt=9):
    x, y, w, h = box
    caption_h = 12 if caption_text else 0
    h_img = h - caption_h if caption_text else h
    img_reader = ImageReader(pil_image if pil_image.mode in ("RGB","L") else pil_image.convert("RGB"))
    c.drawImage(img_reader, x, y + (h - h_img), width=w, height=h_img,
                preserveAspectRatio=True, anchor='c')
    if caption_text:
        c.setFont("Helvetica", caption_pt)
        c.drawCentredString(x + w/2, y + 2, (caption_text or "")[:80])

def debug_draw_grid(c, boxes):
    c.setDash(1,2); c.setLineWidth(0.3)
    for (x,y,w,h) in boxes: c.rect(x, y, w, h, stroke=1, fill=0)
    c.setDash()

def build_pdf_from_images(images, *,
                          title="",
                          rows=4, cols=2,
                          margin_mm=12, gutter_mm=3, header_mm=18, footer_mm=12,
                          show_header=True, show_footer=True,
                          captions=None, caption_pt=9, show_grid=False,
                          pagesize=A4):
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=pagesize)
    page_w, page_h = pagesize
    per_page = rows * cols
    total_pages = max(1, (len(images) + per_page - 1) // per_page)
    idx = 0
    for page_idx in range(1, total_pages + 1):
        boxes = compute_grid(page_w, page_h, rows, cols, margin_mm, gutter_mm, header_mm if show_header else 0, footer_mm if show_footer else 0)
        draw_header_footer(c, page_w, page_h, margin_mm, header_mm, footer_mm, title, show_header, show_footer, page_idx, total_pages)
        if show_grid: debug_draw_grid(c, boxes)
        for b in boxes:
            if idx >= len(images): break
            im = images[idx]; cap = captions[idx] if (captions and idx < len(captions)) else None
            paste_image_contain(c, im, b, caption_text=cap, caption_pt=caption_pt)
            idx += 1
        c.showPage()
    c.save(); buf.seek(0)
    return buf.getvalue()

# ====== UI ======
st.set_page_config(page_title="LILI – PDF Multigrupos (8/img por página)", layout="wide")
st.title("Gerador de PDF de imagens de ultrassom - LILI system")
st.caption("Envie imagens em grupos; gere um PDF por grupo e, se quiser, baixe tudo em ZIP.")

if "groups" not in st.session_state:
    st.session_state.groups = []

st.sidebar.header("Parâmetros de Layout")
title = st.sidebar.text_input("Título do cabeçalho", "Dr. Andrew Costa — ultrassomdermatologico.com")
rows = st.sidebar.number_input("Linhas", 1, 6, 4)
cols = st.sidebar.number_input("Colunas", 1, 4, 2)
margin_mm = st.sidebar.number_input("Margem (mm)", 5.0, 30.0, 12.0, 0.5)
gutter_mm = st.sidebar.number_input("Gutter (mm)", 0.0, 10.0, 3.0, 0.5)
show_header = st.sidebar.checkbox("Exibir cabeçalho", True)
header_h = st.sidebar.number_input("Altura do cabeçalho (mm)", 0.0, 40.0, 18.0, 1.0)
show_footer = st.sidebar.checkbox("Exibir rodapé", True)
footer_h = st.sidebar.number_input("Altura do rodapé (mm)", 0.0, 40.0, 12.0, 1.0)
use_captions = st.sidebar.checkbox("Legenda = nome do arquivo (sem extensão)", False)
caption_pt = st.sidebar.number_input("Tamanho da legenda (pt)", 7, 12, 9, 1)
show_grid = st.sidebar.checkbox("Debug: exibir grade", False)

st.sidebar.markdown("---")
if st.sidebar.button("Limpar todos os grupos"):
    st.session_state.groups = []
    st.sidebar.success("Grupos limpos.")

st.subheader("Adicionar Grupo de Imagens")
up_files = st.file_uploader("Selecione as imagens do grupo", type=["png","jpg","jpeg","webp","bmp"], accept_multiple_files=True)
group_name = st.text_input("Nome do grupo", value=f"Grupo {len(st.session_state.groups)+1}")

c1, c2 = st.columns([1,1])
with c1:
    if st.button("Adicionar grupo", type="primary", use_container_width=True, disabled=not up_files):
        files = []
        for f in up_files:
            try:
                files.append({"name": f.name, "bytes": f.getvalue()})
            except:
                pass
        if files:
            st.session_state.groups.append({"name": group_name.strip() or f"Grupo {len(st.session_state.groups)+1}", "files": files})
            st.success(f"Grupo '{group_name}' adicionado com {len(files)} imagens.")
with c2:
    if st.button("Remover último grupo", use_container_width=True, disabled=len(st.session_state.groups)==0):
        removed = st.session_state.groups.pop(-1)
        st.warning(f"Grupo removido: {removed['name']}")

st.subheader("Grupos preparados")
if not st.session_state.groups:
    st.info("Nenhum grupo adicionado ainda.")
else:
    for i, g in enumerate(st.session_state.groups, start=1):
        st.write(f"**{i}. {g['name']}** — {len(g['files'])} imagens")

st.markdown("---")
b1, b2 = st.columns([1,1])
with b1:
    gen = st.button("Gerar PDFs (um por grupo)", type="primary", use_container_width=True, disabled=len(st.session_state.groups)==0)
with b2:
    zip_all = st.button("Gerar ZIP com todos os PDFs", use_container_width=True, disabled=len(st.session_state.groups)==0)

outputs = []

def build_group_pdf_bytes(group):
    images, captions = [], []
    for f in group["files"]:
        try:
            im = Image.open(io.BytesIO(f["bytes"]))
            images.append(im)
            if use_captions:
                base = os.path.splitext(os.path.basename(f["name"]))[0]
                captions.append(base)
        except:
            continue
    return build_pdf_from_images(images,
        title=title,
        rows=rows, cols=cols,
        margin_mm=margin_mm, gutter_mm=gutter_mm,
        header_mm=header_h, footer_mm=footer_h,
        show_header=show_header, show_footer=show_footer,
        captions=captions if use_captions else None,
        caption_pt=caption_pt,
        show_grid=show_grid,
        pagesize=A4
    )

if gen or zip_all:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    for g in st.session_state.groups:
        try:
            pdf_bytes = build_group_pdf_bytes(g)
            fname = f"{g['name'].strip().replace(' ','_')}_{ts}.pdf"
            outputs.append((g['name'], fname, pdf_bytes))
        except Exception as e:
            st.error(f"Falha ao gerar PDF para grupo '{g['name']}': {e}")

    if outputs:
        st.success(f"{len(outputs)} PDF(s) gerados.")
        for (gname, fname, pdf_bytes) in outputs:
            st.download_button(
                label=f"Baixar PDF — {gname}",
                data=pdf_bytes,
                file_name=fname,
                mime="application/pdf"
            )
        if zip_all:
            zip_buf = io.BytesIO()
            with zipfile.ZipFile(zip_buf, "w", zipfile.ZIP_DEFLATED) as zf:
                for (_gname, fname, pdf_bytes) in outputs:
                    zf.writestr(fname, pdf_bytes)
            zip_buf.seek(0)
            st.download_button(
                label="Baixar ZIP com todos os PDFs",
                data=zip_buf.getvalue(),
                file_name=f"PDFs_ultrassom_{ts}.zip",
                mime="application/zip"
            )

st.caption("LILI — Layout 8 por página com cabeçalho/rodapé, legendas opcionais e múltiplos grupos. © 2025")
