import streamlit as st
from langchain.embeddings import HuggingFaceBgeEmbeddings
from langchain.vectorstores import FAISS
from thefuzz import fuzz
from ast import literal_eval
from streamlit_image_select import image_select

QUERY_PROMPT  = 'Represent this sentence for searching relevant passages: '
METADATA_KEYS = ['From', 'To', 'Cc', 'Date', 'Subject', 'Attachment']

@st.cache_resource
def prep_embeddings():
    model_norm = HuggingFaceBgeEmbeddings(
        model_name="BAAI/bge-base-en",
        model_kwargs={'device': 'cpu'},
        encode_kwargs={'normalize_embeddings': True}
    )
    return model_norm

def prep_db(em):
    return FAISS.load_local('flint_920', em)

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

# https://rjdgrlmrpwnzwmdwgizseanca.s3.us-east-2.amazonaws.com/Treasury1_jp2/Treasury1_0000.png

def format_image_path(text_name):
    directory = '_'.join(text_name.split('_')[:-1])
    fname = text_name.split('.')[0] + '.png'
    return f"https://rjdgrlmrpwnzwmdwgizseanca.s3.us-east-2.amazonaws.com/{directory}_jp2/{fname}"

def display(doc):
    md = doc.metadata
    for key in METADATA_KEYS:
        if md[key] != '[]':
            meta_list = literal_eval(md[key])
            print(type(meta_list))
            st.markdown(f"<small style='text-align: right;'>{key}: <b>{', '.join([escape_markdown(m) for m in meta_list])}</b></small>",unsafe_allow_html=True)
    text_names  = literal_eval(md['image_lookup'])
    image_paths = [format_image_path(tn) for tn in text_names] 
    if len(image_paths) > 1:
        img_select = image_select("See images in this thread", image_paths, captions=[cap.split('/')[-1] for cap in image_paths])
        if img_select:
            st.image(img_select, width=420)
    else:
        st.image(image_paths[0], caption=image_paths[0].split('/')[-1])
    st.markdown("<hr style='width: 75%;margin: auto;'>",unsafe_allow_html=True)