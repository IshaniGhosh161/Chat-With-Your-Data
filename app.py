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

st.set_page_config(page_title="Chat with Doc")
st.header("Chat Application")

# Initialize session state for chat history if it doesn't exist
if 'messages' not in st.session_state:
    st.session_state['messages'] = []

input = st.text_input("Type your query")
uploaded_file = st.file_uploader("Choose an file...",type=['jpeg','jpg','png','pdf','txt','docx','csv','xlsx'])

file_final=None
if uploaded_file:
    file_final=handle_file_question(uploaded_file,input)
else:
    file_final=input

submit = st.button("Generate Answer")
if submit and input:
    st.session_state['messages'].append(("You", input))
    response=get_gemini_response(file_final)
    st.subheader("Response: ")
    # st.write(response)

    generated_text=''
    for chunk in response:
        generated_text+=chunk.text
        st.write(chunk.text)

    st.session_state['messages'].append(("Bot", generated_text))

st.subheader("Chat History")    
for speaker, message in st.session_state['messages']:
    # st.write(f"**{role}**: {text}")
    if speaker == "You":
        st.markdown(
            f'''
            <div style="display: flex; justify-content: flex-start; margin-bottom: 10px;">
                <div style="background-color: #1111; color: #ffffff; padding: 10px; border-radius: 5px;">
                    <b>{speaker}</b>: {message}</div>
            </div>
            ''',
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            f'''
            <div style="display: flex; justify-content: flex-start; margin-bottom: 10px;">
                <div style="background-color: #222; color: #ffffff; padding: 10px; border-radius: 5px;">
                    <b>{speaker}</b>: {message}</div>
            </div>
            ''',
            unsafe_allow_html=True
        )