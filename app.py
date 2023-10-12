import streamlit as st
import utils
import os

css_cdn = """<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet" integrity="sha384-T3c6CoIi6uLrA9TneNEoa7RxnatzjcDSCmG1MXxSR1GAsXEV/Dwwykc2MPK8M2HN" crossorigin="anonymous">"""
js_cdn  = """<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js" integrity="sha384-C6RzsynM9kWDrMNeT87bh95OGNyZPhcTNXj1NW7RuBCsyN/o0jlpcV8Qyq46cDfL" crossorigin="anonymous"></script>"""

st.markdown(css_cdn, unsafe_allow_html=True)
st.markdown(js_cdn, unsafe_allow_html=True)
st.markdown(utils.css,unsafe_allow_html=True)

if os.path.exists('flint_920'): utils.prep_data()
em = utils.prep_embeddings()
db = utils.prep_db(em)

st.markdown('<h1>Flint FOIA Response Search Engine</h1>', unsafe_allow_html=True)
st.markdown(f'<p style="text-align:center">{utils.MAIN_INFO}</p>', unsafe_allow_html=True)
st.expander('Extra info TBD')

search_bar = st.empty()
user_query = search_bar.text_input("Search the emails", key=1) # st.text_input("Search the emails")
suggested = ['local engagement', 'state of emergency', 'water contamination', 'schools', 'lead pipes']
with st.expander('Some suggested queries'):
    for s, col in zip(suggested, st.columns([.2, .2, .25, .15, .2])):
        with col:
            if st.button(s):
                user_query = s
                search_bar.text_input("Search the emails", key=2, value=s)
query = utils.QUERY_PROMPT + user_query
num_responses = st.number_input('Maximum number of documents to see', step=1, min_value=1, value=10)
raw_responses = db.similarity_search(query, k=num_responses+25)
valid_ids = utils.remove_duplicates([rr.page_content for rr in raw_responses])
valid_responses = [raw_responses[i] for i in [vi[0] for vi in valid_ids]][:num_responses]

if user_query != '':
    for vr in valid_responses:
        utils.display(vr)