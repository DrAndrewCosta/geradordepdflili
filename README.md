
# LILI – Ultrassom PDF Multigrupos (Deploy Streamlit)

App pronto para **Streamlit Community Cloud** (ou execução local) para montar PDFs com **8 imagens por página (grade 4×2)**, múltiplos grupos e **ZIP** final.

## Como publicar no Streamlit Community Cloud
1. Crie um repositório no GitHub e envie estes arquivos.
2. No Streamlit Cloud, clique em **New app** → selecione seu repositório.
3. **Main file:** `streamlit_app.py`
4. Deploy.

## Execução local
```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
```

## Recursos
- Grade 4×2 com margens/gutter/cabeçalho/rodapé **paramétricos**
- Encaixe **sem distorção** (contain) e **centralização**
- **Legenda opcional** (nome do arquivo)
- **Debug**: grade visível
- **Múltiplos grupos** → um PDF por grupo e ZIP final

© 2025 – Dr. Andrew Costa / LILI
