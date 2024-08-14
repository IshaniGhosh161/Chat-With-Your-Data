import streamlit as st
import os
from dotenv import load_dotenv
import google.generativeai as genai
from PIL import Image
import pandas as pd
import docx
from PyPDF2 import PdfReader

load_dotenv()

genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))
model = genai.GenerativeModel(model_name="gemini-1.5-pro")
chat=model.start_chat(history=[])

def get_gemini_response(question):  
    # response = model.generate_content(question)
    response = chat.send_message(question,stream=True)
    return response # return response.text

def handle_file_question(uploaded_file,question):
    file_extension = uploaded_file.name.split(".")[-1].lower()

    if file_extension in ['jpeg','jpg','png']:
        image=""
        image = Image.open(uploaded_file)
        st.image(image=image,caption="Uploaded Image",use_column_width=True)
        question=[question,image]
        return question
    
    elif file_extension=='docx':
        doc = docx.Document(uploaded_file)
        full_txt = []
        for i in doc.paragraphs:
            full_txt.append(i.text)
        return question+'\nText:'+'\n'.join(full_txt)
    
    elif file_extension=='txt':
        content = uploaded_file.read().decode('utf-8')
        return question+'\nText:'+content
    
    else:
        pdf_reader= PdfReader(uploaded_file)
        text=''
        for i in pdf_reader.pages:
            text+=i.extract_text()
        return question+'\nText:'+text

st.set_page_config(page_title="Chat App")
st.header("Chat With Your Data")

# input = st.text_input("Type your query")
uploaded_file = st.file_uploader("Choose an file...",type=['jpeg','jpg','png','pdf','txt','docx','csv','xlsx'])
# if uploaded_file:
if "messages" not in st.session_state:
    st.session_state["messages"] = [{"role": "assistant", "content": "How can I help you?"}]

for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

user_query = st.chat_input()
if user_query:
    st.session_state.messages.append({"role": "user", "content": user_query})
    st.chat_message("user").write(user_query)

file_final=None
if uploaded_file and user_query:
    file_final=handle_file_question(uploaded_file,user_query)
else:
    file_final=user_query

# submit = st.button("Generate Answer")
if file_final:
    response=get_gemini_response(file_final)
    st.chat_message("assistant").write(chunk.text for chunk in response)
    st.session_state.messages.append({"role": "assistant", "content": ' '.join(chunk.text for chunk in response)})
