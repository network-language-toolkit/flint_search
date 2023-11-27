import streamlit as st
from thefuzz import fuzz
from sentence_transformers import SentenceTransformer
from pgvector.psycopg import register_vector
import psycopg
import requests
import re

QUERY_PROMPT  = 'Represent this sentence for searching relevant passages: '
METADATA_KEYS = ['From', 'Date', 'To', 'Cc', 'Subject', 'Attachment']
VALID_ARCHIVE = [
    "https://archive.org/details/snyder_flint_emails/MSP004/",
    "https://archive.org/details/snyder_flint_emails/MSP005/",
    "https://archive.org/details/snyder_flint_emails/MSP008/",
    "https://archive.org/details/snyder_flint_emails/MSP009/",
    "https://archive.org/details/snyder_flint_emails/MSP011/",
    "https://archive.org/details/snyder_flint_emails/MSP012/",
    "https://archive.org/details/snyder_flint_emails/Staff_1/",
    "https://archive.org/details/snyder_flint_emails/Staff_10/",
    "https://archive.org/details/snyder_flint_emails/Staff_11/",
    "https://archive.org/details/snyder_flint_emails/Staff_12/",
    "https://archive.org/details/snyder_flint_emails/Staff_13/",
    "https://archive.org/details/snyder_flint_emails/Staff_14/",
    "https://archive.org/details/snyder_flint_emails/Staff_15/",
    "https://archive.org/details/snyder_flint_emails/Staff_16/",
    "https://archive.org/details/snyder_flint_emails/Staff_17/"
]

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

RERANK_SQL = """
WITH semantic_search AS (
    SELECT id, uid, content, embedding, "image_lookup", "From", "Sent", "To", "Cc", "Subject", "Attachment", "thread_index", RANK () OVER (ORDER BY embedding <=> %(embedding)s) AS rank
    FROM documents
    ORDER BY embedding <=> %(embedding)s
    LIMIT 200
),
keyword_search AS (
    SELECT id, uid, content, RANK () OVER (ORDER BY ts_rank_cd(to_tsvector('english', content), query) DESC)
    FROM documents, plainto_tsquery('english', %(query)s) query
    WHERE to_tsvector('english', content) @@ query
    ORDER BY ts_rank_cd(to_tsvector('english', content), query) DESC
    LIMIT 150
)
SELECT
    COALESCE(semantic_search.id, keyword_search.id) AS id,
    semantic_search.uid,
    semantic_search.content,
    semantic_search."image_lookup",
    semantic_search."From",
    semantic_search."Sent",
    semantic_search."To",
    semantic_search."Cc",
    semantic_search."Subject",
    semantic_search."Attachment",
    semantic_search."thread_index",
    COALESCE(1.0 / (%(k)s + semantic_search.rank), 0.0) +
    COALESCE(1.0 / (%(k_comp)s + keyword_search.rank), 0.0) AS score
FROM semantic_search
FULL OUTER JOIN keyword_search ON semantic_search.id = keyword_search.id
ORDER BY score DESC
LIMIT 100
"""

SQL = 'SELECT id, uid, content, "image_lookup", "From", "Sent", "To", "Cc", "Subject", "Attachment", "thread_index" FROM documents ORDER BY embedding <=> %(query_embedding)s LIMIT 50'

K = 70
K_COMP = 100-K

@st.cache_resource
def init_model():
    return SentenceTransformer('BAAI/bge-large-en-v1.5')

def init_db():
    conn = psycopg.connect(
        dbname=st.secrets['manual_db_connection']['dbname'],
        user=st.secrets['manual_db_connection']['user'], 
        password=st.secrets['manual_db_connection']['password'],
        host = st.secrets['manual_db_connection']['host'], 
        port = st.secrets['manual_db_connection']['port'], 
        autocommit=True
        )
    conn.execute('CREATE EXTENSION IF NOT EXISTS vector')
    register_vector(conn)
    return conn

def remove_duplicates(strings, threshold=85):
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
    return text.replace('"', '')

def format_image_path(text_name):
    directory = '_'.join(text_name.split('_')[:-1])
    fname = text_name.split('.')[0] + '.png'
    return f"https://rjdgrlmrpwnzwmdwgizseanca.s3.us-east-2.amazonaws.com/{directory}_jp2/{fname}"

def display(doc):
    md = {key:value.replace("{", "").replace("}", "") for key, value in zip(METADATA_KEYS, doc[4:10])}
    for key in METADATA_KEYS:
        if md[key] != '':
            meta_list = md[key].split('","')
            st.markdown(f"<small style='text-align: right;'>{key}: <b>{', '.join([escape_markdown(m) for m in meta_list])}</b></small>",unsafe_allow_html=True)
    text_names  = doc[3].replace('{', '').replace('}', '').split(',')
    with st.expander('See the Parsed Text'):
        st.markdown(doc[1])
    image_paths = [format_image_path(tn) for tn in text_names] 
    if len(image_paths) > 1:
        image_tabs = st.tabs([ip.split('/')[-1] for ip in image_paths])
        for i,tab in enumerate(image_tabs):
            tab.image(image_paths[i], caption=image_paths[i].split('/')[-1])
    else:
        st.image(image_paths[0], caption=image_paths[0].split('/')[-1])
    repo = re.search(r"([^\/]+)_jp2", image_paths[0]).group(1)
    non_pdf = f"https://archive.org/details/snyder_flint_emails/{repo}"
    if non_pdf in VALID_ARCHIVE:
        link = f'[Click here to explore more on Archive.org]({non_pdf})'
    else:
        pdf_link = f"https://archive.org/details/snyder_flint_emails/{repo}.pdf"
        link = f'[Click here to explore more on Archive.org]({pdf_link})'
    st.markdown(link)
    st.divider()