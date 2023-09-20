# TODO
## Sparse embeddings and rerank
## make pretty :)

import streamlit as st
import utils

em = utils.prep_embeddings()
db = utils.prep_db(em)

st.title('Flint FOIA Response Search Engine')
st.expander('Extra info TBD')

user_query = st.text_input("Search the emails")
query = utils.QUERY_PROMPT + user_query
num_responses = st.number_input('Maximum number of documents to see', step=1, min_value=1, value=10)
raw_responses = db.similarity_search(query, k=num_responses+25)
valid_ids = utils.remove_duplicates([rr.page_content for rr in raw_responses])
valid_responses = [raw_responses[i] for i in [vi[0] for vi in valid_ids]][:num_responses]

if user_query != '':
    for vr in valid_responses:
        utils.display(vr)