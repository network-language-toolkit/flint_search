import streamlit as st
from langchain.embeddings import HuggingFaceBgeEmbeddings
from langchain.vectorstores import FAISS
from thefuzz import fuzz
from ast import literal_eval
import gdown

QUERY_PROMPT  = 'Represent this sentence for searching relevant passages: '
METADATA_KEYS = ['From', 'To', 'Cc', 'Date', 'Subject', 'Attachment']

MAIN_INFO = """
Peter Nadel and Kevin Smith, Tufts University
</br>
</br>
Hundreds of thousands of emails retrieved through FOIA, <i>finally</i> searchable
</br>
</br>
Completely free and open to all
</br>
</br>
"""

css = """
        <style>
            div[data-testid="stImage"] {
                border: 1.5px solid black;
            }
            h1 {
                font-size: 50px;
                text-align: center;
            }
        </style>
        """

@st.cache_data
def prep_data():
    flint_920_url = 'https://drive.google.com/drive/folders/1dXnLDBpVtfSo6SncSdOlidcAMnkbeiG8?usp=sharing'
    gdown.download_folder(flint_920_url, use_cookies=False)

@st.cache_resource
def prep_embeddings():
    model_norm = HuggingFaceBgeEmbeddings(
        model_name="BAAI/bge-base-en",
        model_kwargs={'device': 'cpu'},
        encode_kwargs={'normalize_embeddings': True}
    )
    return model_norm

def prep_db(em):
    return FAISS.load_local('./flint_920', em)

def remove_duplicates(strings, threshold=70):
    unique_strings = []
    for i, string in enumerate(strings):
        is_dup = False
        for unique in unique_strings:
            fuzz_score = fuzz.ratio(string, unique[1])
            if fuzz_score >= threshold:
                is_dup = True
                break
        if not is_dup:
            unique_strings.append((i, string))
    return unique_strings

def escape_markdown(text):
    '''Removes characters which have specific meanings in markdown'''
    MD_SPECIAL_CHARS = "\`*_{}#+$"
    for char in MD_SPECIAL_CHARS:
        text = text.replace(char, '').replace('\t', '')
    return text

def format_image_path(text_name):
    directory = '_'.join(text_name.split('_')[:-1])
    fname = text_name.split('.')[0] + '.png'
    return f"https://rjdgrlmrpwnzwmdwgizseanca.s3.us-east-2.amazonaws.com/{directory}_jp2/{fname}"

def display(doc):
    md = doc.metadata
    for key in METADATA_KEYS:
        if md[key] != '[]':
            meta_list = literal_eval(md[key])
            st.markdown(f"<small style='text-align: right;'>{key}: <b>{', '.join([escape_markdown(m) for m in meta_list])}</b></small>",unsafe_allow_html=True)
    text_names  = literal_eval(md['image_lookup'])
    with st.expander('See the Parsed Email Text'):
        st.markdown(doc.page_content)
    image_paths = [format_image_path(tn) for tn in text_names] 
    if len(image_paths) > 1:
        image_tabs = st.tabs([ip.split('/')[-1] for ip in image_paths])
        for i,tab in enumerate(image_tabs):
            tab.image(image_paths[i], caption=image_paths[i].split('/')[-1])
    else:
        st.image(image_paths[0], caption=image_paths[0].split('/')[-1])
    st.divider()